# -*- coding: utf-8 -*-

#Copyright 2016-2018 Angel Ferran Pousa, DESY
#
#This file is part of VisualPIC.
#
#VisualPIC is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#VisualPIC is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with VisualPIC.  If not, see <http://www.gnu.org/licenses/>.


import os

import numpy as np

import VisualPIC.DataReading.field_readers as fr
from VisualPIC.DataHandling.fields import FolderField
import VisualPIC.DataHandling.unitConverters as uc

class FolderScanner():
    def get_list_of_fields(self, folder_path):
        pass


class OsirisFolderScanner(FolderScanner):
    def __init__(self):
        self.field_reader = fr.OsirisFieldReader()
        #self.unit_converter = uc.OsirisUnitConverter()

    def get_list_of_fields(self, folder_path):
        field_list = []
        folders_in_path = os.listdir(folder_path)
        for folder in folders_in_path:
            if folder == "DENSITY":
                subdir = os.path.join(folder_path, folder)
                available_species = os.listdir(subdir)
                for species in available_species:
                    species_folder = os.path.join(subdir, species)
                    if os.path.isdir(species_folder):
                        species_fields = os.listdir(species_folder)
                        for field in species_fields:
                            field_folder = os.path.join(species_folder, field)
                            if os.path.isdir(field_folder):
                                field_list.append(self._create_field(
                                    field, field_folder, species))
            if folder == "FLD":
                subdir = os.path.join(folder_path, folder)
                domain_fields = os.listdir(subdir)
                for field in domain_fields:
                    field_folder = os.path.join(subdir, field)
                    if os.path.isdir(field_folder):
                        field_list.append(
                            self._create_field(field, field_folder))
        return field_list

    def _create_field(self, field_name, field_folder, species_name=""):
        field_path = self._get_field_path(field_name)
        osiris_field_name = self._get_osiris_field_name(
            field_name)
        field_name = self._get_standard_visualpic_name(
            osiris_field_name)
        fld_files, time_steps = self._get_files_and_timesteps(
            field_folder)
        return FolderField(field_name, field_path, fld_files,
                        time_steps, self.field_reader,
                        'uc', species_name)

    def _get_field_path(self, field_folder_name):
        return '/' + self._get_osiris_field_name(field_folder_name)

    def _get_standard_visualpic_name(self, osiris_name):
        name_relations = {'e1': 'Ez',
                          'e2': 'Ex',
                          'e3': 'Ey',
                          'b1': 'Bz',
                          'b2': 'Bx',
                          'b3': 'By',
                          'charge': 'rho'}
        if osiris_name in name_relations:
            return name_relations[osiris_name]
        else:
            raise ValueError('Unknown data name {}.'.format(osiris_name))

    def _get_osiris_field_name(self, field_folder_name):
        return field_folder_name.replace('-savg', '')

    def _get_files_and_timesteps(self, field_folder_path):
        all_files = os.listdir(field_folder_path)
        h5_files = list()
        for file in all_files:
            if file.endswith(".h5"):
                h5_files.append(os.path.join(field_folder_path, file))
        time_steps = np.zeros(len(h5_files))
        for i, file in enumerate(h5_files):
            time_step = int(file[-9:-3])
            time_steps[i] = time_step
        sort_i = np.argsort(time_steps)
        time_steps = time_steps[sort_i]
        h5_files = np.array(h5_files)[sort_i]
        return h5_files, time_steps