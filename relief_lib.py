# -*- coding: utf-8 -*-
"""
Created on 01.06.2021

Geoprocessing functions and fill algorithms used in the main script relief_fill.py

@author: Nicolas
"""
import gdal
from math import ceil, isnan
import numpy as np
from qgis.gui import QgisInterface, QgsMessageBar

def messageBar():
    return QgsMessageBar()

class MyIface(QgisInterface):
    def __init__(self):
        QgisInterface.__init__(self)

    def messageBar(self):
        return messageBar()

def read_img(inPath):
    """
    FUNCTION loading an image file as GDAL object.
    
    Parameters
    ----------
    inPath : string
        Path to image file

    Returns
    --------
    data_src : gdal.Dataset
    """
    data_src = gdal.Open(inPath)
    return data_src

def write_img(inGdalObject, inTable, outPath):
    """
    PROCEDURE writing a table as a GeoTiff image.
    
    Parameters
    ----------
    inGdalObject : gdal.Dataset
        Source GDAL object
    inTable : array GDAL
        Table to write as image
    outPath : string
        Save path with .tif extension
    """
    driver = gdal.GetDriverByName("GTiff")
    out_data = driver.Create(outPath, inGdalObject.RasterXSize, inGdalObject.RasterYSize, 1, gdal.GDT_Float32) # 1 pour une bande
    out_data.SetGeoTransform(inGdalObject.GetGeoTransform()) # même géotransformation que l'image d'origine
    out_data.SetProjection(inGdalObject.GetProjection())
    out_data.GetRasterBand(1).WriteArray(inTable)
    out_data.FlushCache()
    out_data = None

def x_to_col(inGdalObject, inX):
    """
    FUNCTION returning the column index from the projected geographic X coordinate, using the geotransform parameters.
    The X coordinate has to be in the same CRS as the GDAL dataset.
    
    Parameters
    ----------
    inGdalObject : gdal.Dataset
        Source GDAL Object
    inX : float
        Projected geographic X coordinate
    
    Returns
    -------
    xcol : integer
        Array index corresponding to the pixel column coordinate
    """
    a0 = inGdalObject.GetGeoTransform()[0]
    a1 = inGdalObject.GetGeoTransform()[1]
    xcol = ceil((inX - a0) / a1) - 1
    if xcol < 0 or xcol > (inGdalObject.RasterXSize - 1):
        print("Input coordinate out of range")
    else:
        return xcol

def y_to_row(inGdalObject, inY):
    """
    FUNCTION returning the row index from the projected geographic Y coordinate, using the geotransform parameters.
    The Y coordinate has to be in the same CRS as the GDAL dataset.
    
    Parameters
    ----------
    inGdalObject : gdal.Dataset
        Source GDAL Object
    inY : float
        Projected geographic Y coordinate
    
    Returns
    -------
    yrow : integer
        Array index corresponding to the pixel row coordinate
    """
    a3 = inGdalObject.GetGeoTransform()[3]
    a5 = inGdalObject.GetGeoTransform()[5]
    yrow = ceil((inY - a3) / a5) - 1
    if yrow < 0 or yrow > (inGdalObject.RasterXSize - 1):
        print("Input coordinate out of range")
    else:
        return yrow

def altitude_fill4(inArray, c, r, inType="downstream"):
    """
    FUNCTION crawling a DEM array from the starting point (c=columns, r=row) and returning
    an array with all cells connected to the starting cell that are either above or below it.
    Compares 4 neighbors (no diagonals). 
    
    Parameters
    ----------
    inArray : numpy array
        Array from the GDAL raster band
    c : integer
        Index of the column
    r : integer
        Index of the row
    inType : character string
        Accepted values : "downstream", "upstream"
    
    Returns
    -------
    outArray : numpy array
        Array of all upstream or downstream cells connected to the starting cell.
    """
    # cells already filled
    filled = set()
    # cells to fill
    fill = set()
    fill.add((c, r))
    # array boundaries
    width = inArray.shape[1]-1
    height = inArray.shape[0]-1
    # threshold value to filter the cells
    thr = inArray[r][c]
    # Our output inundation array
    outArray = np.zeros_like(inArray)
    # Loop through and modify the cells which need to be checked
    if inType == "downstream":
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0 or isnan(x) or isnan(y):
                # Do not fill
                continue
            if inArray[y][x] <= thr:
                outArray[y][x] = 1
                filled.add((x, y))
                # Check neighbors
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                if west not in filled:
                    fill.add(west)
                if east not in filled:
                    fill.add(east)
                if north not in filled:
                    fill.add(north)
                if south not in filled:
                    fill.add(south)
        return outArray
    elif inType == "upstream":
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0 or isnan(x) or isnan(y):
                # Do not fill
                continue
            if inArray[y][x] >= thr:
                outArray[y][x] = 1
                filled.add((x, y))
                # Check neighbors
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                if west not in filled:
                    fill.add(west)
                if east not in filled:
                    fill.add(east)
                if north not in filled:
                    fill.add(north)
                if south not in filled:
                    fill.add(south)
        return outArray
    else:
        print('Wrong input parameter "type", select either "downstream" or "upstream"')
    
def altitude_fill8(inArray, c, r, inType="downstream"):
    """
    FUNCTION crawling a DEM array from the starting point (c=columns, r=row) and returning
    an array with all cells connected to the starting cell that are either above or below it.
    Compares 8 neighbors. 
    
    Parameters
    ----------
    inArray : numpy array
        Array from the GDAL raster band
    c : integer
        Index of the column
    r : integer
        Index of the row
    inType : character string
        Accepted values : "downstream", "upstream"
    
    Returns
    -------
    outArray : numpy array
        Array of all upstream or downstream cells connected to the starting cell.
    """
    # cells already filled
    filled = set()
    # cells to fill
    fill = set()
    fill.add((c, r))
    # array boundaries
    width = inArray.shape[1]-1
    height = inArray.shape[0]-1
    # threshold value to filter the cells
    thr = inArray[r][c]
    # Our output inundation array
    outArray = np.zeros_like(inArray)
    # Loop through and modify the cells which need to be checked
    if inType == "downstream":
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0 or isnan(x) or isnan(y):
                # Do not fill
                continue
            if inArray[y][x] <= thr:
                outArray[y][x] = 1
                filled.add((x, y))
                # Check neighbors
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                nw = (x-1, y-1)
                sw = (x-1, y+1)
                ne = (x+1, y-1)
                se = (x+1, y+1)
                if west not in filled:
                    fill.add(west)
                if east not in filled:
                    fill.add(east)
                if north not in filled:
                    fill.add(north)
                if south not in filled:
                    fill.add(south)
                if nw not in filled:
                    fill.add(nw)
                if sw not in filled:
                    fill.add(sw)
                if ne not in filled:
                    fill.add(ne)
                if se not in filled:
                    fill.add(se)
        return outArray
    elif inType == "upstream":
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0 or isnan(x) or isnan(y):
                # Do not fill
                continue
            if inArray[y][x] >= thr:
                outArray[y][x] = 1
                filled.add((x, y))
                # Check neighbors
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                nw = (x-1, y-1)
                sw = (x-1, y+1)
                ne = (x+1, y-1)
                se = (x+1, y+1)
                if west not in filled:
                    fill.add(west)
                if east not in filled:
                    fill.add(east)
                if north not in filled:
                    fill.add(north)
                if south not in filled:
                    fill.add(south)
                if nw not in filled:
                    fill.add(nw)
                if sw not in filled:
                    fill.add(sw)
                if ne not in filled:
                    fill.add(ne)
                if se not in filled:
                    fill.add(se)
        return outArray
    else:
        print('Wrong input parameter "type", select either "downstream" or "upstream"')

def basin_fill(inArray, c, r, inType="downstream"):
    """
    FUNCTION crawling a DEM array from the starting point (c=columns, r=row) and returning
    an array with all cells connected to the starting cell that are CONTINUOUSLY above or below their neighbors.
    
    Parameters
    ----------
    inArray : numpy array
        Array from the GDAL raster band
    c : integer
        Index of the column
    r : integer
        Index of the row
    inType : character string
        Accepted values : "downstream", "upstream"
    
    Returns
    -------
    outArray : numpy array
        Array of all upstream or downstream cells connected to the starting cell within the same basin.
    """
    # cells already filled
    filled = set()
    # cells to fill
    fill = set()
    fill.add((c, r))
    # array boundaries
    width = inArray.shape[1]-1
    height = inArray.shape[0]-1
    # threshold value to filter the cells
    thr = inArray[r][c]
    # Our output inundation array
    outArray = np.zeros_like(inArray)
    # Loop through and modify the cells which need to be checked
    if inType == "downstream":
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0 or isnan(x) or isnan(y):
                # Do not fill
                continue
            if inArray[y][x] <= thr:
                outArray[y][x] = 1
                filled.add((x, y))
                # Check neighbors
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                nw = (x-1, y-1)
                sw = (x-1, y+1)
                ne = (x+1, y-1)
                se = (x+1, y+1)
                if west not in filled and inArray[y][x-1] <= inArray[y][x]:
                    fill.add(west)
                if east not in filled and inArray[y][x+1] <= inArray[y][x]:
                    fill.add(east)
                if north not in filled and inArray[y-1][x] <= inArray[y][x]:
                    fill.add(north)
                if south not in filled and inArray[y+1][x] <= inArray[y][x]:
                    fill.add(south)
                if nw not in filled and inArray[y-1][x-1] <= inArray[y][x]:
                    fill.add(nw)
                if sw not in filled and inArray[y+1][x-1] <= inArray[y][x]:
                    fill.add(sw)
                if ne not in filled and inArray[y-1][x+1] <= inArray[y][x]:
                    fill.add(ne)
                if se not in filled and inArray[y+1][x+1] <= inArray[y][x]:
                    fill.add(se)
        return outArray
    elif inType == "upstream":
        while fill:
            # Grab a cell
            x, y = fill.pop()
            if y == height or x == width or x < 0 or y < 0 or isnan(x) or isnan(y):
                # Do not fill
                continue
            if inArray[y][x] >= thr:
                outArray[y][x] = 1
                filled.add((x, y))
                # Check neighbors
                west = (x-1, y)
                east = (x+1, y)
                north = (x, y-1)
                south = (x, y+1)
                nw = (x-1, y-1)
                sw = (x-1, y+1)
                ne = (x+1, y-1)
                se = (x+1, y+1)
                if west not in filled and inArray[y][x-1] >= inArray[y][x]:
                    fill.add(west)
                if east not in filled and inArray[y][x+1] >= inArray[y][x]:
                    fill.add(east)
                if north not in filled and inArray[y-1][x] >= inArray[y][x]:
                    fill.add(north)
                if south not in filled and inArray[y+1][x] >= inArray[y][x]:
                    fill.add(south)
                if nw not in filled and inArray[y-1][x-1] >= inArray[y][x]:
                    fill.add(nw)
                if sw not in filled and inArray[y+1][x-1] >= inArray[y][x]:
                    fill.add(sw)
                if ne not in filled and inArray[y-1][x+1] >= inArray[y][x]:
                    fill.add(ne)
                if se not in filled and inArray[y+1][x+1] >= inArray[y][x]:
                    fill.add(se)
        return outArray
    else:
        print('Wrong input parameter "type", select either "downstream" or "upstream"')
