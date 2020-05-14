from zephyrus_sc2_parser.events.base_event import BaseEvent


class PlayerStatsEvent(BaseEvent):
    def __init__(self, summary_stats, *args):
        super().__init__(*args)
        self.summary_stats = summary_stats

    def parse_event(self):
        player = self.player
        gameloop = self.event['_gameloop']
        event = self.event
        summary_stats = self.summary_stats

        if not player:
            return

        self.player.supply = event['m_stats']['m_scoreValueFoodUsed'] // 4096
        self.player.supply_cap = event['m_stats']['m_scoreValueFoodMade'] // 4096

        if gameloop != self.game.game_length:
            if self.player.supply >= self.player.supply_cap:
                self.player.supply_block += 112

        self.player.resources_collected['minerals'] = (
            event['m_stats']['m_scoreValueMineralsCurrent'] +
            event['m_stats']['m_scoreValueMineralsUsedInProgressArmy'] +
            event['m_stats']['m_scoreValueMineralsUsedInProgressEconomy'] +
            event['m_stats']['m_scoreValueMineralsUsedInProgressTechnology'] +
            event['m_stats']['m_scoreValueMineralsUsedCurrentArmy'] +
            event['m_stats']['m_scoreValueMineralsUsedCurrentEconomy'] +
            event['m_stats']['m_scoreValueMineralsUsedCurrentTechnology'] +
            event['m_stats']['m_scoreValueMineralsLostArmy'] +
            event['m_stats']['m_scoreValueMineralsLostEconomy'] +
            event['m_stats']['m_scoreValueMineralsLostTechnology']
        )

        self.player.resources_collected['gas'] = (
            event['m_stats']['m_scoreValueVespeneCurrent'] +
            event['m_stats']['m_scoreValueVespeneUsedInProgressArmy'] +
            event['m_stats']['m_scoreValueVespeneUsedInProgressEconomy'] +
            event['m_stats']['m_scoreValueVespeneUsedInProgressTechnology'] +
            event['m_stats']['m_scoreValueVespeneUsedCurrentArmy'] +
            event['m_stats']['m_scoreValueVespeneUsedCurrentEconomy'] +
            event['m_stats']['m_scoreValueVespeneUsedCurrentTechnology'] +
            event['m_stats']['m_scoreValueVespeneLostArmy'] +
            event['m_stats']['m_scoreValueVespeneLostEconomy'] +
            event['m_stats']['m_scoreValueVespeneLostTechnology']
        )

        unspent_resources = self.player.unspent_resources
        collection_rate = self.player.collection_rate

        if gameloop != 1:
            unspent_resources['minerals'].append(
                event['m_stats']['m_scoreValueMineralsCurrent']
            )
            unspent_resources['gas'].append(
                event['m_stats']['m_scoreValueVespeneCurrent']
            )

            collection_rate['minerals'].append(
                event['m_stats']['m_scoreValueMineralsCollectionRate']
            )
            collection_rate['gas'].append(
                event['m_stats']['m_scoreValueVespeneCollectionRate']
            )

        if gameloop == self.game.game_length:
            summary_stats['supply_block'][player.player_id] = round(self.player.supply_block / 22.4, 1)

            summary_stats['resources_lost']['minerals'][player.player_id] = event['m_stats']['m_scoreValueMineralsLostArmy']
            summary_stats['resources_lost']['gas'][player.player_id] = event['m_stats']['m_scoreValueVespeneLostArmy']

            summary_stats['resources_collected']['minerals'][player.player_id] = self.player.resources_collected['minerals']
            summary_stats['resources_collected']['gas'][player.player_id] = self.player.resources_collected['gas']

            player_minerals = unspent_resources['minerals']
            player_gas = unspent_resources['gas']
            summary_stats['avg_unspent_resources']['minerals'][player.player_id] = round(
                sum(player_minerals)/len(player_minerals), 1
            )
            summary_stats['avg_unspent_resources']['gas'][player.player_id] = round(
                sum(player_gas)/len(player_gas), 1
            )

            player_minerals_collection = collection_rate['minerals']
            player_gas_collection = collection_rate['gas']
            summary_stats['avg_resource_collection_rate']['minerals'][player.player_id] = round(
                sum(player_minerals_collection)/len(player_minerals_collection), 1
            )
            summary_stats['avg_resource_collection_rate']['gas'][player.player_id] = round(
                sum(player_gas_collection)/len(player_gas_collection), 1
            )

            total_collection_rate = summary_stats['avg_resource_collection_rate']['minerals'][player.player_id] + summary_stats['avg_resource_collection_rate']['gas'][player.player_id]
            total_avg_unspent = summary_stats['avg_unspent_resources']['minerals'][player.player_id] + summary_stats['avg_unspent_resources']['gas'][player.player_id]
            player_sq = player.calc_sq(unspent_resources=total_avg_unspent, collection_rate=total_collection_rate)
            summary_stats['sq'][player.player_id] = player_sq

            current_workers = event['m_stats']['m_scoreValueWorkersActiveCount']
            workers_produced = summary_stats['workers_produced'][player.player_id]
            summary_stats['workers_lost'][player.player_id] = workers_produced - current_workers

        return summary_stats
