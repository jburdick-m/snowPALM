import sys
import os
import netCDF4 as nc4
from datetime import datetime, date, timedelta
from dateutil.parser import parse
import numpy as np
from scipy import interpolate
import csv
from osgeo import gdal, osr, ogr

pars = {}
pars['StartDate'] = sys.argv[1]
pars['EndDate'] = sys.argv[2]
pars['StationName'] = sys.argv[3]
pars['Latitude'] = sys.argv[4]
pars['Longitude'] = sys.argv[5]
pars['ForcingSetName'] = sys.argv[6]

pars['ElevFile'] = 'Preprocess/GIS/DTM_small.tif'
pars['ForcingDir'] = 'Preprocess/Forcing/' + pars['ForcingSetName']
pars['OutputDir'] = 'Output/Forcing_double_check'


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)
        

if __name__ == '__main__':

    StartDate = parse(pars['StartDate']).date()
    EndDate = parse(pars['EndDate']).date()
    
    ds = gdal.Open(pars['ElevFile'])
    geotransform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    band = ds.GetRasterBand(1)
    Elev = band.ReadAsArray().astype(float)
    ds = None
    
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(4326)
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromProj4(projection)
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(float(pars['Latitude']), float(pars['Longitude']))
    point.Transform(coordTrans)
    
    xi = point.GetX()
    yi = point.GetY()
    
    Year_vec = []
    Month_vec = []
    Day_vec = []
    Hour_vec = []
    Precip_vec = []
    Rain_vec = []
    Snow_vec = []
    AirT_vec = []
    Pres_vec = []
    RH_vec = []
    Wind_vec = []
    WindAngle_vec = []
    DSWRF_vec = []
    DLWRF_vec = []
    PET_vec = []
    
    for TS in daterange(StartDate, EndDate + timedelta(days=1)):
    
        yyyy = str(TS.year)
        mm = str(TS.month)
        if len(mm) < 2:
            mm = '0' + mm
        dd = str(TS.day)
        if len(dd) < 2:
            dd = '0' + dd
                
        ifname = pars['ForcingDir'] + '/' + yyyy + '/' + mm + '/' + dd + '.nc'
        print('Reading ' + ifname)
        ds = nc4.Dataset(ifname)
       
        x = ds['X'][:]
        y = np.flipud(ds['Y'][:])
        Precip = ds['Precip'][:]
        Rain = ds['Rain'][:]
        Snow = ds['Snow'][:]
        AirT = ds['AirT'][:]
        Pres = ds['Pres'][:]
        RH = ds['RH'][:]
        Wind = ds['WindSpeed'][:]
        WindAngle = ds['WindDir'][:]
        DSWRF = ds['Shortwave'][:]
        DLWRF = ds['Longwave'][:]
        PET = ds['PET'][:]
        
        Year_vec.append(TS.year)
        Month_vec.append(TS.month)
        Day_vec.append(TS.day)
        
        if AirT.shape[0] == 24:
            for i in range(24):
            
                Precip_sub = Precip[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                Precip_vec.append(f(xi, yi))
                
                Data_sub = Rain[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                Rain_vec.append(f(xi, yi))
                
                Data_sub = Snow[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                Snow_vec.append(f(xi, yi))
                
                Data_sub = AirT[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                AirT_vec.append(f(xi, yi))
                
                Data_sub = Pres[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                Pres_vec.append(f(xi, yi))
                
                Data_sub = RH[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                RH_vec.append(f(xi, yi))
                
                Data_sub = Wind[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                Wind_vec.append(f(xi, yi))
                
                Data_sub = WindAngle[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                WindAngle_vec.append(f(xi, yi))
                
                Data_sub = DSWRF[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                DSWRF_vec.append(f(xi, yi))
                
                Data_sub = DLWRF[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                DLWRF_vec.append(f(xi, yi))
                
                Data_sub = PET[i,:,:]
                f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
                PET_vec.append(f(xi, yi))
                
                Hour_vec.append(i)
               
        elif AirT.shape[0] == 1:
        
            Data_sub = Precip[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            Precip_vec.append(f(xi, yi)[0])
            
            Data_sub = Rain[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            Rain_vec.append(f(xi, yi)[0])
            
            Data_sub = Snow[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            Snow_vec.append(f(xi, yi)[0])
            
            Data_sub = AirT[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            AirT_vec.append(f(xi, yi)[0])
            
            Data_sub = Pres[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            Pres_vec.append(f(xi, yi)[0])
            
            Data_sub = RH[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            RH_vec.append(f(xi, yi)[0])
            
            Data_sub = Wind[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            Wind_vec.append(f(xi, yi)[0])
            
            Data_sub = WindAngle[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            WindAngle_vec.append(f(xi, yi)[0])
            
            Data_sub = DSWRF[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            DSWRF_vec.append(f(xi, yi)[0])
            
            Data_sub = DLWRF[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            DLWRF_vec.append(f(xi, yi)[0])
            
            Data_sub = PET[0,:,:]
            f = interpolate.interp2d(x, y, np.flipud(Data_sub), kind='linear')
            PET_vec.append(f(xi, yi)[0])
        
            Hour_vec.append(np.nan)
            
        # from matplotlib import pyplot as plt
        # plt.imshow(AirT[0,:,:])
        # plt.colorbar()
        # plt.show()
            
        ds = None
        
    
    f = interpolate.interp2d(x, y, np.flipud(Elev), kind='linear')
    Elev = f(xi, yi)[0]
    
    
    if not os.path.exists(pars['OutputDir']):
        os.makedirs(pars['OutputDir'])
    
    OFName = pars['OutputDir'] + '/' + pars['StationName'] + '(' + pars['ForcingSetName'] + ').csv'
    print('Writing ' + OFName)
    with open(OFName, 'w',newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        topline = [pars['StationName'], float(pars['Latitude']), float(pars['Longitude']), int(Elev)]
        header = ['Year', 'Month', 'Day', 'Hour', 'Precip', 'Rain', 'Snow', 'AirT', 'Pres', 'RH', 'Wind', 'WindAngle', 'DSWRF', 'DLWRF', 'PET']
        units = ['', '', '', '', 'mm', 'mm', 'mm', 'C', 'Pa', 'pct', 'm/s', 'degrees', 'W/m2', 'W/m2', 'mm']
        writer.writerow(topline)
        writer.writerow(header)
        writer.writerow(units)
       
        for row in range(len(AirT_vec)):
            data_ = [Year_vec[row], Month_vec[row], Day_vec[row], Hour_vec[row], Precip_vec[row], Rain_vec[row], Snow_vec[row], AirT_vec[row], Pres_vec[row], RH_vec[row], Wind_vec[row], WindAngle_vec[row], DSWRF_vec[row], DLWRF_vec[row], PET_vec[row]]
            writer.writerow(data_)
    