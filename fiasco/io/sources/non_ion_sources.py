"""
Source classes for CHIANTI filetypes not attached to ions
"""
import os
import numpy as np
import h5py
import astropy.units as u
from astropy.table import Column
import fortranformat
import periodictable
import fiasco

from ..generic import GenericParser

__all__ = ['AbundParser','IoneqParser','IpParser']


class AbundParser(GenericParser):
    filetype = 'abund'
    dtypes = [int,float,str]
    units = [None,u.dimensionless_unscaled,None]
    headings = ['atomic number','abundance relative to H','element']
    fformat = fortranformat.FortranRecordReader('(I3,F7.3,A5)')

    def __init__(self,abundance_filename):
        self.abundance_filename = abundance_filename
        self.full_path = os.path.join(fiasco.defaults['chianti_dbase_root'],
                                      'abundance', self.abundance_filename)

    def postprocessor(self,df):
        df['abundance relative to H'] = 10.**(df['abundance relative to H'] 
                                              - df['abundance relative to H'][df['atomic number']==1])
        # repair missing data
        if df['element'][0] == '':
            col = []
            for atomic_number in df['atomic number']:
                col.append(periodictable.elements[int(atomic_number)].symbol.lower())
            df['element'] = Column(col) 
        df.meta['abundance_filename'] = self.abundance_filename
        return df

    def to_hdf5(self,hf,df):
        dataset_name = os.path.splitext(os.path.basename(self.abundance_filename))[0]
        footer = """{}
------------------
{}
        """.format(dataset_name,df.meta['footer'])
        for row in df:
            grp_name = '/'.join([row['element'].lower(),'abundance'])
            if grp_name not in hf:
                grp = hf.create_group(grp_name)
                grp.attrs['footer'] = ''
            else:
                grp = hf[grp_name]
            grp.attrs['footer'] += footer
            if dataset_name not in grp:
                ds = grp.create_dataset(dataset_name,data=row['abundance relative to H'])
                ds.attrs['unit'] = df['abundance relative to H'].unit.to_string()


class IoneqParser(GenericParser):
    filetype = 'ioneq'
    dtypes = [int,int,float,float]
    units = [None,None,u.K,u.dimensionless_unscaled]
    headings = ['atomic number','ion','temperature','ionization fraction']

    def __init__(self,ioneq_filename):
        self.ioneq_filename = ioneq_filename
        self.full_path = os.path.join(fiasco.defaults['chianti_dbase_root'],
                                      'ioneq', self.ioneq_filename)
        
    def preprocessor(self,table,line,index):
        if index==0:
            num_entries = int(line.strip().split()[0])
            self.fformat_temperature = fortranformat.FortranRecordReader('{}F6.2'.format(num_entries))
            self.fformat_ioneq = fortranformat.FortranRecordReader('2I3,{}E10.2'.format(num_entries))
        elif index==1:
            self.temperature = 10.**np.array(self.fformat_temperature.read(line),dtype=float)
        else:
            line = self.fformat_ioneq.read(line)
            line = line[:2] + [self.temperature,np.array(line[2:],dtype=float)] 
            table.append(line)
        
    def postprocessor(self,df):
        df.meta['ioneq_filename'] = self.ioneq_filename
        return df

    def to_hdf5(self,hf,df):
        dataset_name = os.path.splitext(os.path.basename(self.ioneq_filename))[0]
        for row in df:
            el = periodictable.elements[int(row['atomic number'])].symbol.lower()
            ion = int(row['ion'])
            grp_name = '/'.join([el,'{}_{}'.format(el,ion),'ioneq'])
            if grp_name not in hf:
                grp = hf.create_group(grp_name)
                grp.attrs['footer'] = ''
            else:
                grp = hf[grp_name]
            if dataset_name not in grp:
                sub_grp = grp.create_group(dataset_name)
                sub_grp.attrs['footer'] = df.meta['footer']
                ds = sub_grp.create_dataset('temperature',data=row['temperature'])
                ds.attrs['unit'] = df['temperature'].unit.to_string()
                ds = sub_grp.create_dataset('ionization fraction',data=row['ionization fraction'])
                ds.attrs['unit'] = df['ionization fraction'].unit.to_string()


class IpParser(GenericParser):
    filetype = 'ip'
    dtypes = [int,int,float]
    units = [None,None,1/u.cm]
    headings = ['atomic number','ion','ionization potential']

    def __init__(self,ip_filename):
        self.ip_filename = ip_filename
        self.full_path = os.path.join(fiasco.defaults['chianti_dbase_root'],
                                      'ip',self.ip_filename)

    def postprocessor(self,df):
        df.meta['ip_filename'] = self.ip_filename
        return df

    def to_hdf5(self,hf,df):
        dataset_name = os.path.splitext(os.path.basename(self.ip_filename))[0]
        footer = """{}
------------------
{}
        """.format(dataset_name,df.meta['footer'])
        for row in df:
            el = periodictable.elements[int(row['atomic number'])].symbol.lower()
            ion = int(row['ion'])
            grp_name = '/'.join([el,'{}_{}'.format(el,ion),'ip'])
            if grp_name not in hf:
                grp = hf.create_group(grp_name)
                grp.attrs['footer'] = ''
            else:
                grp = hf[grp_name]
            grp.attrs['footer'] += footer
            if dataset_name not in grp:
                ds = grp.create_dataset(dataset_name,data=row['ionization potential'])
                ds.attrs['unit'] = df['ionization potential'].unit.to_string()


