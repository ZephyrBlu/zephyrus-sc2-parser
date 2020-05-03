from zephyrus_sc2_parser.events.base_event import BaseEvent
from zephyrus_sc2_parser.gamedata.ability_data import abilities


class AbilityEvent(BaseEvent):
    def __init__(self, summary_stats, *args):
        super().__init__(*args)
        self.summary_stats = summary_stats

    def _get_game_object(self):
        event = self.event

        if 'None' in event['m_data'] or 'TargetUnit' not in event['m_data']:
            return None

        unit_game_id = event['m_data']['TargetUnit']['m_tag']

        for obj_id, obj in self.player.objects.items():
            if obj.tag == event['m_data']['TargetUnit']['m_snapshotUnitLink']:
                break

        if unit_game_id in self.player.objects:
            return self.player.objects[unit_game_id]
        return None

    def parse_event(self):
        player = self.player
        event = self.event
        gameloop = self.gameloop
        summary_stats = self.summary_stats

        if not player:
            return

        if self.type == 'NNet.Game.SCmdEvent':
            if event['m_abil']:
                if event['m_abil']['m_abilLink'] and type(event['m_abil']['m_abilCmdIndex']) is int:
                    obj = self._get_game_object()
                    queued = False
                    if 'm_cmdFlags' in event:
                        bitwise = event['m_cmdFlags'] & 2
                        if bitwise == 2:
                            queued = True

                    ability = (
                        event['m_abil']['m_abilLink'],
                        event['m_abil']['m_abilCmdIndex'],
                        obj,
                        queued,
                    )
                else:
                    ability = None
                player.active_ability = ability

                # inject
                if player.active_ability and player.active_ability[0] == 111 and obj:
                    # ~1sec
                    if not obj.abilities_used:
                        obj.abilities_used.append((abilities[111], gameloop))
                    elif (gameloop - obj.abilities_used[-1][1]) > 22 or player.active_ability[3]:
                        obj.abilities_used.append((abilities[111], gameloop))

                if player.active_ability and player.active_ability[0] == 717:
                    pass

                # # MULE and Supply Drop
                # if player.active_ability and (player.active_ability[0] == 90 or player.active_ability[0] == 113):
                #     obj.abilities_used.append((abilities[player.active_ability], gameloop))

        return summary_stats
