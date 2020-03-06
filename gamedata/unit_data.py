units = {
    'Protoss': {
        'Probe': {
            'obj_id': [106],
            'priority': 33,
            'type': ['unit', 'worker'],
            'mineral_cost': 50,
            'gas_cost': 0,
            'supply': 1,
        },
        'Zealot': {
            'obj_id': [95],
            'priority': 39,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 0,
            'supply': 2,
        },
        'Stalker': {
            'obj_id': [96],
            'priority': 60,
            'type': ['unit'],
            'mineral_cost': 125,
            'gas_cost': 50,
            'supply': 2,
        },
        'Sentry': {
            'obj_id': [99],
            'priority': 87,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 100,
            'supply': 2,
        },
        'Adept': {
            'obj_id': [439],
            'priority': 57,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 25,
            'supply': 2,
        },
        'AdeptPhaseShift': {
            'obj_id': [1036],
            'priority': 54,
            'type': ['unit'],  # 'temporary'
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'HighTemplar': {
            'obj_id': [97],
            'priority': 93,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 150,
            'supply': 2,
        },
        'DarkTemplar': {
            'obj_id': [98],
            'priority': 56,
            'type': ['unit'],
            'mineral_cost': 125,
            'gas_cost': 125,
            'supply': 2,
        },
        'Archon': {
            'obj_id': [163],
            'priority': 45,
            'type': ['unit'],

            # cost values are 2 HT merging
            # not sure how to dynamically calc cost
            'mineral_cost': 100,
            'gas_cost': 300,

            'supply': 4,
        },
        'Observer': {
            'obj_id': [104],
            'priority': 36,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 75,
            'supply': 1,
        },
        'ObserverSiegeMode': {
            'obj_id': [104],
            'priority': 36,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 75,
            'supply': 1,
        },
        'WarpPrism': {
            'obj_id': [103],
            'priority': 69,
            'type': ['unit'],
            'mineral_cost': 250,
            'gas_cost': 0,
            'supply': 2,
        },
        'WarpPrismPhasing': {
            'obj_id': [103],
            'priority': 69,
            'type': ['unit'],
            'mineral_cost': 250,
            'gas_cost': 0,
            'supply': 2,
        },
        'Immortal': {
            'obj_id': [105],
            'priority': 44,
            'type': ['unit'],
            'mineral_cost': 275,
            'gas_cost': 100,
            'supply': 4,
        },
        'Colossus': {
            'obj_id': [23],
            'priority': 48,
            'type': ['unit'],
            'mineral_cost': 300,
            'gas_cost': 200,
            'supply': 6,
        },
        'Disruptor': {
            'obj_id': [440],
            'priority': 72,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 150,
            'supply': 3,
        },
        'Phoenix': {
            'obj_id': [100],
            'priority': 81,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 100,
            'supply': 2,
        },
        # Phoenix pick up state
        # 'Phoenix': {
        #     'obj_id': [100],
        #     'priority': 81,
        #     'type': ['unit'],
        #     'mineral_cost': 150,
        #     'gas_cost': 100,
        #     'supply': 2,
        # },
        'VoidRay': {
            'obj_id': [102],
            'priority': 78,
            'type': ['unit'],
            'mineral_cost': 250,
            'gas_cost': 150,
            'supply': 4,
        },
        'Oracle': {
            'obj_id': [184, 423],
            'priority': 84,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 150,
            'supply': 3,
        },
        'OracleStasisTrap': {
            'obj_id': [951],
            'priority': 0,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Tempest': {
            'obj_id': [185],
            'priority': 50,
            'type': ['unit'],
            'mineral_cost': 250,
            'gas_cost': 175,
            'supply': 5,
        },
        'Carrier': {
            'obj_id': [101],
            'priority': 51,
            'type': ['unit'],
            'mineral_cost': 350,
            'gas_cost': 250,
            'supply': 6,
        },
        'Interceptor': {
            'obj_id': None,
            'priority': None,
            'type': ['unit'],
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Mothership': {
            'obj_id': [30],
            'priority': 96,
            'type': ['unit'],
            'mineral_cost': 400,
            'gas_cost': 400,
            'supply': 8,
        }
    },
    'Terran': {
        'SCV': {
            'obj_id': [67],
            'priority': 58,
            'type': ['unit', 'worker'],
            'mineral_cost': 50,
            'gas_cost': 0,
            'supply': 1,
        },
        'MULE': {
            'obj_id': [381],
            'priority': 56,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Marine': {
            'obj_id': [70],
            'priority': 78,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 0,
            'supply': 1,
        },
        'Reaper': {
            'obj_id': [71],
            'priority': 70,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 50,
            'supply': 1,
        },
        'Marauder': {
            'obj_id': [73],
            'priority': 76,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 25,
            'supply': 2,
        },
        'Ghost': {
            'obj_id': [72],
            'priority': 82,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 125,
            'supply': 2,
        },
        'Hellion': {
            'obj_id': [75],
            'priority': 66,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 0,
            'supply': 2,
        },
        'Hellbat': {
            'obj_id': [75],
            'priority': 6,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 0,
            'supply': 2,
        },
        'WidowMine': {
            'obj_id': [436, 448],
            'priority': 54,
            'type': ['unit'],
            'mineral_cost': 75,
            'gas_cost': 25,
            'supply': 2,
        },
        'WidowMineBurrowed': {
            'obj_id': [436, 448],
            'priority': 54,
            'type': ['unit'],
            'mineral_cost': 75,
            'gas_cost': 25,
            'supply': 2,
        },
        'SiegeTank': {
            'obj_id': [55],
            'priority': 74,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 125,
            'supply': 3,
        },
        'SiegeTankSieged': {
            'obj_id': [55],
            'priority': 74,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 125,
            'supply': 3,
        },
        'Thor': {
            'obj_id': [74],
            'priority': 52,
            'type': ['unit'],
            'mineral_cost': 300,
            'gas_cost': 200,
            'supply': 6,
        },
        'ThorAP': {
            'obj_id': [74],
            'priority': 52,
            'type': ['unit'],
            'mineral_cost': 300,
            'gas_cost': 200,
            'supply': 6,
        },
        'VikingFighter': {
            'obj_id': [56],
            'priority': 68,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 75,
            'supply': 2,
        },
        'VikingAssault': {
            'obj_id': [56],
            'priority': 68,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 75,
            'supply': 2,
        },
        'Medivac': {
            'obj_id': [76],
            'priority': 60,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 100,
            'supply': 2,
        },
        'Liberator': {
            'obj_id': [437, 449],
            'priority': 72,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 150,
            'supply': 3,
        },
        'LiberatorAG': {
            'obj_id': [437, 449],
            'priority': 72,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 150,
            'supply': 3,
        },
        'Raven': {
            'obj_id': [78],
            'priority': 84,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 200,
            'supply': 2,
        },
        'AutoTurret': {
            'obj_id': [53],
            'priority': 2,
            'type': ['building'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Battlecruiser': {
            'obj_id': [79],
            'priority': 80,
            'type': ['unit'],
            'mineral_cost': 400,
            'gas_cost': 300,
            'supply': 6,
        },
    },
    'Zerg': {
        'Larva': {
            'obj_id': [177, 188],
            'priority': 58,
            'type': ['unit'],
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': None,
        },
        'Egg': {
            'obj_id': [125],
            'priority': 54,
            'type': ['unit'],
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': None,
        },
        'Drone': {
            'obj_id': [126],
            'priority': 60,
            'type': ['unit', 'worker'],
            'mineral_cost': 50,
            'gas_cost': 0,
            'supply': 1,
        },
        'Overlord': {
            'obj_id': [128],
            'priority': 72,
            'type': ['unit', 'supply'],
            'mineral_cost': 100,
            'gas_cost': 0,
            'supply': 0,
        },
        'Queen': {
            'obj_id': [148],
            'priority': 101,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 0,
            'supply': 2,
        },
        'Zergling': {
            'obj_id': [127],
            'priority': 68,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 0,
            'supply': 0.5,
        },
        'Baneling': {
            'obj_id': [29],
            'priority': 82,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 25,
            'supply': 0,
        },
        'Roach': {
            'obj_id': [132],
            'priority': 80,
            'type': ['unit'],
            'mineral_cost': 75,
            'gas_cost': 25,
            'supply': 2,
        },
        'Ravager': {
            'obj_id': [178],
            'priority': 92,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 75,
            'supply': 0,
        },
        'TransportOverlordCocoon': {
            'obj_id': [181],
            'priority': 1,
            'type': ['unit', 'supply'],
            'mineral_cost': 25,
            'gas_cost': 25,
            'supply': 0,
        },
        'OverlordCocoon': {
            'obj_id': [150],
            'priority': 1,
            'type': ['unit', 'supply'],
            'mineral_cost': 50,
            'gas_cost': 50,
            'supply': 0,
        },
        'Overseer': {
            'obj_id': [151],
            'priority': 74,
            'type': ['unit', 'supply'],
            'mineral_cost': 50,
            'gas_cost': 50,
            'supply': 0,
        },
        'OverseerSiegeMode': {
            'obj_id': [151],
            'priority': 74,
            'type': ['unit', 'supply'],
            'mineral_cost': 50,
            'gas_cost': 50,
            'supply': 0,
        },
        'OverlordTransport': {
            'obj_id': [177],
            'priority': 73,
            'type': ['unit', 'supply'],
            'mineral_cost': 25,
            'gas_cost': 25,
            'supply': 0,
        },
        'Hydralisk': {
            'obj_id': [129],
            'priority': 70,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 50,
            'supply': 2,
        },
        'LurkerMP': {
            'obj_id': [173],
            'priority': 90,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 100,
            'supply': 1,
        },
        'LurkerMPEgg': {
            'obj_id': [175],
            'priority': 54,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 100,
            'supply': 1,
        },
        'LurkerMPBurrowed': {
            'obj_id': [173],
            'priority': 90,
            'type': ['unit'],
            'mineral_cost': 50,
            'gas_cost': 100,
            'supply': 0,
        },
        'Mutalisk': {
            'obj_id': [130],
            'priority': 76,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 100,
            'supply': 2,
        },
        'Corruptor': {
            'obj_id': [134],
            'priority': 84,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 100,
            'supply': 2,
        },
        'SwarmHostMP': {
            'obj_id': [441],
            'priority': 86,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 75,
            'supply': 3,
        },
        'LocustMP': {
            'obj_id': [678],
            'priority': 54,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'LocustMPFlying': {
            'obj_id': [907],
            'priority': 56,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'LocustMPPrecursor': {
            'obj_id': [678],
            'priority': 54,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Infestor': {
            'obj_id': [133],
            'priority': 94,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 150,
            'supply': 2,
        },
        'InfestedTerransEgg': {
            'obj_id': [187],
            'priority': 54,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'InfestorTerran': {
            'obj_id': [27],
            'priority': 66,
            'type': ['unit'],  # temporary
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Viper': {
            'obj_id': [442],
            'priority': 96,
            'type': ['unit'],
            'mineral_cost': 100,
            'gas_cost': 200,
            'supply': 3,
        },
        'Ultralisk': {
            'obj_id': [131],
            'priority': 88,
            'type': ['unit'],
            'mineral_cost': 300,
            'gas_cost': 200,
            'supply': 6,
        },
        'BroodLord': {
            'obj_id': [136],
            'priority': 78,
            'type': ['unit'],
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'BroodlingEscort': {
            'obj_id': None,
            'priority': None,
            'type': ['unit'],
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'Broodling': {
            'obj_id': [404],
            'priority': 62,
            'type': ['unit'],
            'mineral_cost': 0,
            'gas_cost': 0,
            'supply': 0,
        },
        'RavagerCocoon': {
            'obj_id': [180],
            'priority': 54,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 75,
            'supply': 1,
        },
        'BanelingCocoon': {
            'obj_id': [28],
            'priority': 54,
            'type': ['unit'],
            'mineral_cost': 25,
            'gas_cost': 25,
            'supply': 0,
        },
        'BroodLordCocoon': {
            'obj_id': [135],
            'priority': 1,
            'type': ['unit'],
            'mineral_cost': 150,
            'gas_cost': 150,
            'supply': 2,
        },
    }
}
