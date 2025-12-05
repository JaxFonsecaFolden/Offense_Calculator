# --- Mecklenburg County: Criminal Justice Services ---
# --- Research & Planning Personalized Python Module ---

import pandas as pd
import numpy as np
import re
from typing import Optional, Literal, Union, List

class DataSource:
    
    class_order = (
        'A', 'B1', 'B2', 'C', 'D', 'E', 'F', 'H', 'I',
        'A1', '1', '2', '3', 'FNC', 'MNC', '??', ''
    )
    class_rank = {cls: i for i, cls in enumerate(class_order)}

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
        for col in initial_df.select_dtypes(include=['object']).columns:
            initial_df[col] = initial_df[col].astype(str).str.strip()
        self._data = initial_df
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
        Data ("calculated data" | "original data")(OPTIONAL)
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
        selected_codes = np.select(
            condlist=[condition_3digit],
            choicelist=[choice_3digit],
            default=choice_4digit
        )
        self._data[newCol_Name] = pd.to_numeric(
            selected_codes,
            errors='coerce'
        )
        self._Col_Code = newCol_Name

       
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
        File_OffenseCodes = File_OffenseCodes.apply(lambda x: x.astype(str).str.strip() if x.dtype == "object" else x)
        File_colNull = File_colNull if File_colNull is not None else 'CL'
        Data_colNull = Data_colNull if Data_colNull is not None else self._Col_Class
        lookup_data = File_OffenseCodes[['CODE', File_colNull]].copy()
        lookup_data = lookup_data.drop_duplicates(subset=['CODE'], keep='last')
        lookup_data['CODE'] = pd.to_numeric(lookup_data['CODE'], errors='coerce') 
        temp_col = f'{Data_colNull}_original'
        if temp_col not in self._data.columns:
            self._data = self._data.rename(columns={Data_colNull: temp_col})
        if Value_Exception is not None:
            if isinstance(Value_Exception, str):
                exceptions = [Value_Exception.upper()]
            else:
                exceptions = [item.upper() for item in Value_Exception]
            self._data[temp_col] = self._data[temp_col].astype(str).str.upper()
            self._data[temp_col] = self._data[temp_col].replace('', pd.NA)
            self._data.loc[self._data[temp_col].isin(exceptions), temp_col] = pd.NA
        rows_b4_drop = len(self._data)
        if self._droppedRows is None:
            self._droppedRows = self._data[self._data[self._Col_Code].isna()].copy()
        else:
            self._droppedRows = pd.concat([
                self._droppedRows, 
                self._data[self._data[self._Col_Code].isna()].copy()
            ]).drop_duplicates(keep='last')
        data_to_fill = self._data.loc[self._data[self._Col_Code].notna()].copy()
        print(f"Dropped {len(self._droppedRows) / rows_b4_drop * 100:.2f}% rows where '{self._Col_Code}' was missing.")
        merged_df = pd.merge(
            data_to_fill,
            lookup_data,
            left_on=self._Col_Code,
            right_on='CODE',
            how='left'
        )
        merged_df[Data_colNull] = merged_df[temp_col].fillna(merged_df[File_colNull])
        merged_df = merged_df.drop(columns=[temp_col, 'CODE', File_colNull], errors='ignore')
        self._data = pd.concat([merged_df, self._droppedRows.drop(columns=[temp_col], errors='ignore')], ignore_index=True)
        
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
        elif self._data is not None: 
            df_to_export = self._data
        else: 
            print("No data exist in cjs.DataSource() object")
            return
        if File_Name is None:
            if isinstance(self._CSV_File, str):
                folder, file_path = self._CSV_File.rsplit('/', 1)
                File_Name = file_path.rsplit('.', 1)[0]
            else:
                File_Name = 'pd_DataFrame'
        df_to_export = df_to_export.dropna(how='all')
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
        self, *,
        Group_By: Optional[Union[str, List[str]]] = None, 
        Find_Class: Optional[Union[str, List[str]]] = None
    ):
        """
        Calculates the highest offense within the given parameter(s),
        Sorting order: class, code
            
        Parameters
        ----------
        Group_By (str | list) (REQUIRED | OPTIONAL)
            Specifies the method in which grouping should be processed by, 
            *Optional* and defaulted to _Col_PrimKey if initially specified,
            *Required* if _Col_Primkey is not initially specified
        Find_Class (str | list) (OPTIONAL)
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
            if hasattr(self, '_Col_PrimKey') and self._Col_PrimKey is not None:
                Group_By = self._Col_PrimKey
            else:
                print("Group_By parameter needs to be filled or _Col_PrimKey needs to be filled.")
                return
        group_list = [Group_By] if isinstance(Group_By, str) else Group_By
        class_targets = None
        if Find_Class is not None:
            class_targets = [fc.upper().strip() for fc in ([Find_Class] if isinstance(Find_Class, str) else Find_Class)]
        valid_class_set = set(self.class_order).difference({'??', ''})
        sorted_classes = sorted(list(valid_class_set), key=len, reverse=True)
        def extract_class_components(class_string):
            """(1) Pulls the highest predicted class value or (2) the matching Find_Class value of all predicted values"""
            if pd.isna(class_string):
                return ''
            s = str(class_string).upper()
            s = re.sub(r'FELONY|MISDEMEANOR|CLASS|W/G', '', s) 
            extracted_components = []
            s_working = s
            i = 0
            while i < len(s_working):
                matched = False
                for cls in sorted_classes:
                    if s_working.startswith(cls, i):
                        extracted_components.append(cls)
                        i += len(cls)
                        matched = True
                        break 
                if not matched and s_working[i] == '/':
                    extracted_components.append('/')
                    i += 1
                    matched = True
                if not matched:
                    i += 1
            result = ''.join(extracted_components).strip('/')
            return result
        df = self._data.copy()
        df["_orig_order"] = range(len(df))
        df['_clean_class'] = df[self._Col_Class].apply(extract_class_components)
        MAX_RANK_VALUE = len(self.class_order) 
        best_target_rank = MAX_RANK_VALUE
        if class_targets:
            target_ranks = [self.class_rank.get(cls, MAX_RANK_VALUE) for cls in class_targets]
            best_target_rank = min(target_ranks)
        df['base_rank'] = df['_clean_class'].map(self.class_rank)
        composite_mask = df['_clean_class'].str.contains('/', na=False)
        df_composite = df[composite_mask].copy()
        if not df_composite.empty:
            df_exploded = df_composite.assign(
                component_class=df_composite['_clean_class'].str.split('/') 
            ).explode('component_class')
            df_exploded['component_class'] = df_exploded['component_class'].str.strip()
            df_exploded['comp_rank'] = df_exploded['component_class'].map(self.class_rank)
            if class_targets:
                df_exploded = df_exploded[
                    df_exploded['comp_rank'] >= best_target_rank 
                ].copy()
            min_ranks = df_exploded.dropna(subset=['comp_rank']).groupby(level=0)['comp_rank'].min()
            df.loc[min_ranks.index, 'base_rank'] = min_ranks
        df['base_rank'] = df['base_rank'].fillna(MAX_RANK_VALUE).astype(np.int64) 
        df_filtered = df.copy() 
        if class_targets:
            patterns = [r'\b' + re.escape(target) + r'\b' for target in class_targets]
            combined_pattern = '|'.join(patterns)
            mask = df_filtered['_clean_class'].str.contains(combined_pattern, na=False, regex=True)
            df_filtered = df_filtered[mask].copy()
            if df_filtered.empty:
                self._newData = None
                print(f"No offenses found containing the specified Find_Class target(s): {', '.join(class_targets)}")
                return
        df_filtered = df_filtered[df_filtered['base_rank'] != MAX_RANK_VALUE].copy()
        if df_filtered.empty:
            self._newData = None
            print("No valid offenses remain after filtering and rank verification.")
            return
        MAX_CODE_VALUE = 9999 
        df_filtered['sort_code'] = df_filtered[self._Col_Code].astype(float).fillna(MAX_CODE_VALUE)
        df_filtered = df_filtered.sort_values(
            by=["base_rank", "sort_code", "_orig_order"],
            ascending=[True, True, True] 
        )
        indexes_minCode = df_filtered.groupby(group_list).head(1).index
        newData = df_filtered.loc[indexes_minCode].copy()
        col_to_drop = ['base_rank', '_orig_order', 'sort_code', '_clean_class']
        newData = newData.drop(
            columns=col_to_drop, 
            errors='ignore'
        ) 
        self._newData = newData