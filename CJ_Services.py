# from OffenseDict_Class import OffenseMap
import pandas as pd
import numpy as np
import re
from typing import Optional, Literal, Union, List

class DataSource:
    def __init__(
        self, *, 
        CSV_File: Union[str, pd.DataFrame], 
        Col_PrimKey: Optional[str] = None, 
        Col_Class: str, 
        Col_Code: str
    ):
        
        """
        Processes CSV File into python, allowing users to utilize the DataSource class with ease.
        
        Attributes
        ----------
        CSV_File (str | pandas.DataFrame())
            File path, must be CSV
        Col_PrimKey (str | None)
            The column header containing the primary key of the dataset
        Col_Class (str)
            The column header containing the offense class/degree
        Col_Code (str)
            The column header containing the offense code
            
        Local Variables
        ----------
        **_data** : (pandas.DataFrame()) 
            > Stores the initialized data and any post data non-permanent method executions
        **_newData** : (pandas.DataFrame())
            > Stores the data after a non-permanent method is executed
        **_droppedRows** : (pandas.DataFrame())
            > Stores dropped rows from the DataSource.Fill_BlankCol() function
        """
        
        self._CSV_File = CSV_File
        if Col_PrimKey is not None:
            self._Col_PrimKey = Col_PrimKey
        self._Col_Class = Col_Class
        self._Col_Code = Col_Code
        if isinstance(CSV_File, str):
            initial_df = pd.read_csv(CSV_File, low_memory=False)
        else: initial_df = CSV_File
        self._data = initial_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        self._newData = None
        self._droppedRows = None
   
    def Get_Data(
        self, 
        Data: Optional[Literal["calculated data", "original data"]] = None
    ):
        
        """
        Retrieves data into python to utilize Pandas Library methods.
        
        Parameters
        ----------
        Data: ("calculated data" | "original data")(OPTIONAL)
            Specifies which type of data retrieved
                
        Returns
        ----------
        pandas.DataFrame()
            If data exist, returning data as a pandas DataFrame
        None
            If data does not exist, returning None
        """
        
        if Data == "calculated data":
            if self._newData is not None:
                print("Returning Calculated Data")
                return self._newData
            print("Data has not been calculated")
            return
        elif Data == "original data":
            if self._data is not None:
                print("Returning Original Data")
                return self._data
            print("Data has not been intialized")
            return
        elif Data is None:
            if self._newData is not None:
                print("Returning Calculated Data")
                return self._newData
            elif self._data is not None:
                print("Returning Original Data")
                return self._data
            print("No Existing Dataset")
            return
       
    def SliceCol_Code(self):
        
        """
        Support Method: Extracts and Stardardizes offense codes to its 3 or 4 digit values.
                
        Returns
        ----------
        New Column
            Creates a new column within the pandas.DataFrame() as "Code (4)" column
        """
        
        newCol_Name = 'Code (4)'
        col_code = self._data[self._Col_Code]
        cleaned_codes = col_code.astype(str).fillna('')
        cleaned_codes = cleaned_codes.str.lstrip('0')
        prefix_3digit = ('91', '92', '93', '94', '95', '96', '97', '98')
        condition_3digit = cleaned_codes.str.startswith(prefix_3digit)
        choice_3digit = cleaned_codes.str[:3]
        choice_4digit = cleaned_codes.str[:4]
        self._data[newCol_Name] = np.select(
            condlist=[condition_3digit],
            choicelist=[choice_3digit],
            default=choice_4digit
        )
        self._Col_Code = newCol_Name
        self._data[newCol_Name] = pd.to_numeric(self._data[newCol_Name], errors='coerce')
       
    def Fill_BlankCol(
        self, *,
        File_OffenseCodes: pd.DataFrame,
        File_colNull: Optional[str] = None,
        Data_colNull: Optional[str] = None,
        Value_Exception: Optional[Union[str, List[str]]] = None
    ):
        
        """
        Backfills missing data pertaining to the Offence Codes dataset provided by NC State.
            
        Parameters
        ----------
        File_OffenseCodes (pandas.DataFrame())
            Specifies the variable containing the Offense Codes in a pandas.DataFrame()
        File_colNull (str) (OPTIONAL)
            The column header in the Offense Codes dataset that contains the needed values
        Data_colNull (str) (OPTIONAL)
            The column header of the 
        Value_Exception (str | list[str]) (OPTIONAL)
                
        Returns
        ----------
        New Column
            Creates and fills a new column containing existing/unaltered data and filling in missing data
        """
        
        if 'Code (4)' not in self._data.columns:
            self.SliceCol_Code()
        File_OffenseCodes = File_OffenseCodes.apply(lambda x: x.astype(str).str.strip())
        if File_colNull is None:
            File_colNull = 'CL'
        lookup_data = File_OffenseCodes[['CODE', File_colNull]].copy()
        lookup_data = lookup_data.drop_duplicates(subset=['CODE'], keep='last')
        lookup_data['CODE'] = pd.to_numeric(lookup_data['CODE'], errors='coerce')
        if Data_colNull is None:
            Data_colNull = self._Col_Class
        else:
            Data_colNull = self._Col_Class
        temp_col = f'{self._Col_Class}_original'
        if Value_Exception is not None:
            if isinstance(Value_Exception, list):
                Value_Exception = [item.upper() for item in Value_Exception]
            else:
                Value_Exception = Value_Exception.upper()
            self._data[Data_colNull] = self._data[Data_colNull].str.upper()
            self._data[Data_colNull] = self._data[Data_colNull].replace(to_replace=Value_Exception, value=np.nan)
        self._data.rename(columns={Data_colNull: temp_col}, inplace=True)
        rows_b4_drop = len(self._data)
        if self._droppedRows is None:
            self._droppedRows = self._data[self._data[self._Col_Code].isna()]
        rows_after_drop = self._data.loc[self._data[self._Col_Code].notna()].copy()
        print(f"Dropped {rows_b4_drop - len(rows_after_drop)} rows where '{self._Col_Code}' was missing.")
        merged_df = pd.merge(
            rows_after_drop,
            lookup_data,
            left_on=self._Col_Code,
            right_on='CODE',
            how='left'
        )
        merged_df[Data_colNull] = merged_df[temp_col].fillna(merged_df[File_colNull])
        merged_df.drop(columns=[temp_col, 'CODE', File_colNull], inplace=True, errors='ignore')
        self._data = merged_df
        
    def Get_Dropped(self):
        
        """
        Check Method: Provides data that was dropped from the cjs.Fill_BlankCol() method.
                
        Returns
        ----------
        pandas.DataFrame()
            If dataset was processed by the cjs.Fill_BlankCol() and function dropped columns
        None
            If no columns were dropped
        """
        
        if self._droppedRows is None:
            print("No values were dropped")
        return self._droppedRows
   
    def Export_File(
        self, 
        Folder_Path: Optional[str] = None, 
        File_Name: Optional[str] = None
    ):
        
        """
        Exports processed dataset to a CSV file format.
            
        Parameters
        ----------
        Folder_Path (str) (OPTIONAL)
            Specifies the folder in which file should be exported too
        File_Name (str) (OPTIONAL)
            Specifies name of processed dataset, default is the PROCESSED_[Original Dataset Name]
                
        Returns
        ----------
        CSV UTF-8
            CSV file that is comma deliminated
        """
        
        if self._newData is not None:
            df_to_export = self._newData
        else:
            df_to_export = self._data
        if File_Name is None:
            if isinstance(self._CSV_File, str):
                folder, file_path = self._CSV_File.rsplit('/', 1)
                File_Name = file_path.rsplit('.', 1)[0]
            else:
                File_Name = 'pd_DataFrame'
        df_to_export.dropna(how='all', inplace=True)
        df_to_export = df_to_export.copy()
        df_to_export = df_to_export.replace(np.nan, '')
        df_to_export = df_to_export.astype(str)
        if Folder_Path is None:
            Folder_Path = '_'
        elif Folder_Path is not None:
            if Folder_Path[-1] != '/':
                Folder_Path = Folder_Path + '/'
        df_to_export.to_csv(
            f"{Folder_Path}PROCESSED_{File_Name}.csv", 
            index=False, 
            encoding='utf-8'
        )
        if Folder_Path == '_':
            print(f'Exported as "{Folder_Path}PROCESSED_{File_Name}.csv"')
            return print()
        print(f'Exported in "{Folder_Path}" folder as "PROCESSED_{File_Name}.csv"')
        return print()
   
    def Calc_HighestOffense(
        self, 
        Group_By: Optional[str] = None, 
        Find_Class: Optional[str] = None
    ):
        
        """
        Calculates the highest offense within the given parameter(s)
            
        Parameters
        ----------
        Group_By (str) (REQUIRED | OPTIONAL)
            Specifies the method in which grouping should be processed by, 
            *Optional* and defaulted to _Col_PrimKey if initially specified,
            *Required* if _Col_Primkey is not initially specified
        Find_Class (str) (OPTIONAL)
            Specifies is a certain class/degree needs to be extracted,
            default is the highest class of given parameter
                
        Returns
        ----------
        pandas.DataFrame()
            An extracted dataset of the most serious offenses (given its parameter) 
            within the dataset provided, and assigned to the _newData local variable
        """
        
        if 'Code (4)' not in self._data.columns:
            self.SliceCol_Code()
        if Group_By is None:
            Group_By = self._Col_PrimKey
        indexes_minCode = self._data.groupby(Group_By)[self._Col_Code].idxmin()
        newData = self._data.loc[indexes_minCode]
        self._newData = newData
        if Find_Class is not None:
            Find_Class = Find_Class.upper()
            search_pattern = r'\b' + re.escape(Find_Class) + r'\b'
            if self._newData is not None:
                self._newData[self._Col_Class] = self._newData[self._Col_Class].astype(str).str.upper()
                newData = self._newData[self._newData[self._Col_Class].str.contains(search_pattern, regex=True, na=False)]
                newData = pd.DataFrame(newData)
                self._newData = newData