from unittest import TestCase

from app.integrations.fpl.kit_assets import (
    get_fpl_kit_url,
    get_fpl_kit_url_from_bootstrap,
)
from app.schemas.fpl import FPLPlayerPosition


class FPLKitAssetTests(TestCase):
    def test_outfield_kit_uses_team_code(self):
        self.assertEqual(
            get_fpl_kit_url(
                team_code=3,
                player_position=FPLPlayerPosition.DEFENDER,
            ),
            "https://fantasy.premierleague.com/dist/img/shirts/standard/"
            "shirt_3-110.webp",
        )

    def test_goalkeeper_kit_uses_goalkeeper_variant(self):
        self.assertEqual(
            get_fpl_kit_url(
                team_code=3,
                player_position=FPLPlayerPosition.GOALKEEPER,
            ),
            "https://fantasy.premierleague.com/dist/img/shirts/standard/"
            "shirt_3_1-110.webp",
        )

    def test_kit_url_can_be_resolved_from_bootstrap_team(self):
        self.assertEqual(
            get_fpl_kit_url_from_bootstrap(
                bootstrap={"teams": [{"id": 1, "code": 3}]},
                team_id=1,
                player_position=FPLPlayerPosition.FORWARD,
            ),
            "https://fantasy.premierleague.com/dist/img/shirts/standard/"
            "shirt_3-110.webp",
        )

    def test_missing_bootstrap_team_has_no_kit_url(self):
        self.assertIsNone(
            get_fpl_kit_url_from_bootstrap(
                bootstrap={"teams": []},
                team_id=1,
                player_position=FPLPlayerPosition.FORWARD,
            )
        )
