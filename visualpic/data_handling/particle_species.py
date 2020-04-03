"""
This file is part of VisualPIC.

The module contains the definitions of the ParticleSpecies class.

Copyright 2016-2020, Angel Ferran Pousa.
License: GNU GPL-3.0.
"""


from visualpic.data_handling.derived_particle_data_definitions import (
    derived_particle_data_definitions, get_definition)


class ParticleSpecies():

    """Class providing access to the data of a particle species"""

    def __init__(self, species_name, components_in_file, species_timesteps,
                 species_files, data_reader, unit_converter):
        """
        Initialize the particle species.

        Parameters
        ----------

        species_name : str
            Name of the particle species.

        components_in_file : list
            List of string containing the names (in VisualPIC convention) of
            the particle components available in the data files for this
            species.

        species_timesteps : array
            A sorted numpy array numbering all the timesteps containing data
            of this particle species.

        species_file : list
            A sorted list of strings (same orders as species_timesteps)
            containing the path to each data file of this species.

        data_reader : ParticleReader
            An instance of a ParticleReader of the corresponding simulation
            code.

        unit_converter : UnitConverter
            An instance of a UnitConverter of the corresponding simulation
            code.
        """
        self.species_name = species_name
        self.components_in_file = components_in_file
        self.derived_components = self._determine_available_derived_components(
            components_in_file)
        self.timesteps = species_timesteps
        self.species_files = species_files
        self.data_reader = data_reader
        self.unit_converter = unit_converter

    def get_data(self, time_step, components_list, data_units=None,
                 time_units=None):
        """
        Get the species data of the requested components and time step and in
        the specified units.

        Parameters
        ----------

        time_step : int
            Time step at which to read the data. This is the time step number
            as generated by the simulation code, not the index of the time
            step list.

        components_list : list
            List of strings containing the names of the components to be read.

        data_units : list
            (Optional) List of strings containing the desired unis in which to
            return the data. If specified, it should have the same lenght as
            'components_list'. If not, the data will be returned in the same
            units as in the file.

        time_units : str
            (Optional) Units in which to return the time information of the
            data. If not specified, the time data will be returned in the same
            units as in the data file.

        Returns
        -------
        A dictionary containing the particle data. The keys correspond to the
        names of each of the requested components. Each key stores a tuple
        where the first element is the data array and the second is the 
        metadata dictionary.
        """
        # Check that the length of components_list and data_units match
        units_are_specified = data_units is not None
        if (units_are_specified and (len(components_list) != len(data_units))):
            len_comp = len(components_list)
            len_units = len(data_units)
            raise ValueError(
                'Lenght of components list ({})'.format(len_comp) +
                ' and data units list ({}) do not match.'.format(len_units))
        # Separate components to read from file from those which are derived
        comp_to_read = []
        derived_components = []
        if units_are_specified:
            comp_to_read_units = []
            derived_components_units = []
        else:
            comp_to_read_units = None
            derived_components_units = None
        for i, component in enumerate(components_list):
            if component in self.components_in_file:
                comp_to_read.append(component)
                if units_are_specified:
                    comp_to_read_units.append(data_units[i])
            elif component in self.derived_components:
                derived_components.append(component)
                if units_are_specified:
                    derived_components_units.append(data_units[i])
            else:
                available_comps = self.get_list_of_available_components()
                raise ValueError(
                    "Component '{}' not found. ".format(component) +
                    "Available components are {}.".format(available_comps))
        # Read data from file
        file_path = self._get_file_path(time_step)
        folder_data = self._get_file_data(file_path, comp_to_read,
                                          comp_to_read_units, time_units)
        # Compute derived data
        derived_data = self._calculate_derived_data(
            file_path, derived_components, derived_components_units,
            time_units)
        # Join in a single dictionary
        data = {**folder_data, **derived_data}
        return data

    def get_list_of_available_components(self, include_tags=False):
        """
        Returns a list of strings with the names of all available components.
        """
        all_components = self.components_in_file + self.derived_components
        if not include_tags and 'tag' in all_components:
            all_components.remove('tag')
        return all_components

    def _get_file_path(self, time_step):
        """Get the file path corresponding to the specified time step."""
        ts_i = self.timesteps.tolist().index(time_step)
        return self.species_files[ts_i]

    def _get_file_data(self, file_path, components_list, data_units,
                       time_units):
        """Read the specified components from a data file."""
        data = self.data_reader.read_particle_data(
            file_path, self.species_name, components_list)
        data = self._convert_data_units(data, components_list, data_units,
                                        time_units)
        return data

    def _calculate_derived_data(self, file_path, data_list, target_data_units,
                                time_units):
        """Calculate the specifield derived components."""
        derived_data_dict = {}
        for name in data_list:
            data_def = get_definition(name)
            data_name = data_def['name']
            data_units = data_def['units']
            required_data_list = data_def['requirements']
            required_data_units = ['SI'] * len(required_data_list)
            required_data = self._get_file_data(
                file_path, required_data_list, required_data_units, time_units)
            derived_data = data_def['recipe'](required_data)
            derived_data_md = required_data[required_data_list[0]][1]
            derived_data_md['units'] = data_units
            derived_data_dict[data_name] = (derived_data, derived_data_md)
        derived_data_dict = self._convert_data_units(
            derived_data_dict, data_list, target_data_units, time_units)
        return derived_data_dict

    def _convert_data_units(self, data, components_list, data_units=None,
                            time_units=None):
        """Convert the data and time units of the supplied particle data."""
        if data_units is not None:
            units_dict = dict(zip(components_list, data_units))
            # Perform data unit conversion
            data = self.unit_converter.convert_particle_data_units(
                data, target_data_units=units_dict,
                target_time_units=time_units)
        return data

    def _determine_available_derived_components(self, components_in_file):
        """
        Determine the available derived components for the data available in
        the file.
        """
        available_derived_comps = []
        for component in derived_particle_data_definitions:
            if set(component['requirements']).issubset(components_in_file):
                available_derived_comps.append(component['name'])
        return available_derived_comps
