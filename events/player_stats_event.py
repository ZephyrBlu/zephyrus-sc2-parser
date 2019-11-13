from .base_event import BaseEvent


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
            summary_stats['resources_lost']['minerals'][player.player_id] = event['m_stats']['m_scoreValueMineralsLostArmy']
            summary_stats['resources_lost']['gas'][player.player_id] = event['m_stats']['m_scoreValueVespeneLostArmy']

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
            summary_stats['workers_lost'][player.player_id] = workers_produced + 12 - current_workers

        return summary_stats
