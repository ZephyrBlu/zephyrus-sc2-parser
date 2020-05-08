import os
import copy
import csv
from pathlib import Path
from base_unit_data import units
from base_building_data import buildings
from base_ability_data import abilities
from base_upgrade_data import upgrades
from protocols import protocols

path = Path('version_data')
prev_protocol = {
    'unit': 0,
    'building': 0,
    'ability': 0,
}

for file_path in path.iterdir():
    if file_path.is_file():
        version = int(file_path.name[:5])
        if 'units' in file_path.name:
            version_data = {
                'unit': copy.deepcopy(units),
                'building': copy.deepcopy(buildings),
            }
        elif 'abilities' in file_path.name:
            version_data = {'ability': copy.deepcopy(abilities)}
            new_version_data = {}
        else:
            continue

        with open(file_path) as data:
            reader = csv.reader(data)

            for row in reader:
                obj_id = int(row[0])
                obj_name = row[1]

                obj_race = False
                for data_type, data in version_data.items():
                    if data_type == 'unit' or data_type == 'building':
                        for race, obj_type_data in data.items():
                            if obj_name in obj_type_data:
                                obj_race = race
                                break

                        if obj_race:
                            version_data[data_type][obj_race][obj_name]['obj_id'] = obj_id
                            break
                    elif data_type == 'ability':
                        if obj_name in abilities:
                            new_version_data[obj_id] = {'ability_name': obj_name}
                            new_version_data[obj_id].update(abilities[obj_name])
                    else:
                        continue

        for i in range(0, len(protocols)):
            prot_version = protocols[i]

            if prev_protocol[data_type] < prot_version <= version:
                if not os.path.isdir(f'zephyrus_sc2_parser/gamedata/{prot_version}'):
                    os.mkdir(f'zephyrus_sc2_parser/gamedata/{prot_version}')
                    Path(f'zephyrus_sc2_parser/gamedata/{prot_version}/__init__.py').touch()

                for data_type, data in version_data.items():
                    if data_type == 'unit' or data_type == 'building':
                        data_name = f'{data_type}s'
                        write_data = version_data[data_type]
                    elif data_type == 'ability':
                        data_name = 'abilities'
                        write_data = new_version_data
                    else:
                        continue

                    with open(f'zephyrus_sc2_parser/gamedata/{prot_version}/{data_type}_data.py', 'w') as version_file:
                        version_file.write(f'# Version {prot_version}\n{data_name} = {write_data}')

                with open(f'zephyrus_sc2_parser/gamedata/{prot_version}/upgrade_data.py', 'w') as version_file:
                    version_file.write(f'# Version {prot_version}\nupgrades = {upgrades}')

            elif prot_version > version:
                prev_protocol[data_type] = protocols[i - 1]
                break
