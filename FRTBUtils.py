"""
Some common frtb.net utility functions

Copyright © 2024 frtb.net limited

Author: Alan Skea, frtb.net limited

Contact us at <info@frtb.net> or via our website at <https://frtb.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pandas as pd

_typeMap = {
    'str'       : str,
    'bool'      : bool,
    'float64'   : float,
    'int64'     : int
}

_fillnaMap = {
    'str'       : '',
    'bool'      : False,
    'float64'   : 0.0,
    'int64'     : 0
}


def _toList(l, n=None):
    lst = []
    i = 0

    for e in l:
        if e == '' and (n is None or i >= n):
            break
        else:
            lst.append(e)
            i += 1

    return lst


def extractKeyedData(sourceName, df, dataTypes, listKeys=[], arrayKeys=[], rowHdrKeys=[], colHdrKeys=[], addIndex=None, addColumns=None):
    """
        Extract data from a DataFrame using a key structure

        :param sourceName: Name of the source of the data
        :param df: pandas DataFrame containing the data
        :param dataTypes: Dictionary of data types for the keys ('str', 'float64', 'int64')
        :param listKeys: List of keys that are lists
        :param arrayKeys: List of keys that are arrays
        :param rowHdrKeys: List of keys that are row headers
        :param colHdrKeys: List of keys that are column headers
        :param addIndex: Dictionary of keys and expressions to eval to add to the index
        :param addColumns: Dictionary of keys and expressions to eval add to the columns

        :return: Dictionary of key-value
    """

    # idx is the row index for the array, if there is one
    # cols is the column index for the array, if there is one
    # __processKey gets these fromt the enclosing scope
    dataDict = {}
    k = None
    name = ''
    idx = []
    cols = None
    values = []


    def __processKey():
        #
        # deal with the collected data from the previous key
        #     - create a DataFrame if the key is in arrayKeys
        #     - create a Series if the key is in listKeys
        #     - otherwise it is a scalar value
        #
        if k in arrayKeys:
            if len(idx) == 0:
                dataDict[k] = pd.DataFrame(values, index=None, columns=cols)
            else:
                dataDict[k] = pd.DataFrame(values, index=idx, columns=cols)

            dataDict[k].index.set_names(name)
        elif k in listKeys:
            if k in colHdrKeys:
                if len(cols) > 1:
                    dataDict[k] = pd.Series(values, index=cols, name=k)
                else:
                    dataDict[k] = pd.Series(values, name=cols[0])
            elif k in rowHdrKeys:
                dataDict[k] = pd.Series(values, index=idx, name=k)
            else:
                dataDict[k] = pd.Series(values, index=None, name=k)

            dataDict[k].index.set_names(name)
        else :
            # Scalar value
            #
            dataDict[k] = values[0]


    ##################
    #
    # Main part of function
    #
    for _, r in df.iterrows():
        # column 0 in the name of this data, i.e. the key
        # if it's empty then we are still processing the previous key
        # and if there is no previous key then we have an error
        if r.at[0] == '':
            if k == None:
                raise ValueError('No initial key defined in config')
        else:
            if not k is None:
                # we have a new key so process the previous one
                __processKey()

            # initialise for the new key
            name = k = r.at[0]
            idx = []
            cols = None
            values = []

            # if we have columnheaderes on this item then collect them
            if k in colHdrKeys:
                if k in rowHdrKeys:
                    name = r.at[1]
                    cols = _toList(r.loc[2:])
                else:
                    cols = _toList(r.loc[1:])

                continue

        col = 1

        # if we have row headers then collect the hearder on this row
        if k in rowHdrKeys:
            if r.at[col] != '':     # can this happen except on last row?
                idx.append(r.at[col])

            col += 1

        if not k in arrayKeys:
            if r.shape[0] > col + 1 and r.at[col + 1] != '':
                # Horizontal list
                if k in colHdrKeys:
                    values = _toList(r.loc[col:],len(cols) + col - 1)
                else:
                    values = _toList(r.loc[col:])
            elif r.at[col] != '':
                # Vertical list or scalar
                values.append(r.at[col])
        elif k in colHdrKeys and not r.iloc[col:len(cols) + col].eq('').all():
            # Must be an array row
            values.append(_toList(r.loc[col:], len(cols) + col - 1))
        elif not r.eq('').all():
                values.append(_toList(r.loc[col:]))

    # process the last key
    __processKey()

    # add the requested indexes and columns
    if not addIndex is None:
        for k, v in addIndex.items():
            try:
                dataDict[k].index = eval(v)
            except Exception as err:
                raise ValueError(f"Error setting index on '{k}' with '{v}' in source '{sourceName}': {err}")

    if not addColumns is None:
        for k, v in addColumns.items():
            try:
                dataDict[k].rename(columns=dict(zip(dataDict[k].columns, eval(v))), inplace=True)
            except Exception as err:
                raise ValueError(f"Error column index on '{k}' with '{v}' in source '{sourceName}': {err}")

    # Now set the types and fill NAs where needed
    for k, v in dataDict.items():
        if k in dataTypes:
            if not k in listKeys + arrayKeys:
                # scalar value
                #
                try:
                    dataDict[k] = _typeMap[dataTypes[k]](v)
                    # dataDict[k] = _typeMap[dataTypes[k]](v[0])
                except:
                    raise ValueError(f"Bad type conversion from '{v[0]}' (type: {type(v[0])} -> {_typeMap[dataTypes[k]]})' for key '{k}' in  source '{sourceName}'")
            else:
                try:
                    if isinstance(dataTypes[k], dict):
                        fillMap = dict((k1, _fillnaMap[v1]) for k1,v1 in dataTypes[k].items())
                        dataDict[k] = dataDict[k].astype(dataTypes[k]).fillna(fillMap)
                    else:
                        dataDict[k] = dataDict[k].astype(dataTypes[k]).fillna(_fillnaMap[dataTypes[k]])
                except:
                    raise ValueError(f"Bad type conversion from (type: {type(dataDict[k])})' for key '{k}' in  source '{sourceName}'")


    return dataDict
