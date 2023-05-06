import dataclasses
from pathlib import Path
from typing import Any, Dict, List

import codem
import stactools.core.create
from pystac import Asset, Item, Link, MediaType
from stactask import Task
from stactask.exceptions import InvalidInput


class Coreg(Task):  # type: ignore
    name = "codem-coreg"
    description = "Registers STAC Item Assets to a foundational source."

    def run_codem(
        self, foundation_href: str, aoi_href: str, parameters: Dict[str, Any]
    ) -> str:
        codem_run_config = codem.CodemRunConfig(
            FND_FILE=foundation_href,
            AOI_FILE=aoi_href,
            DSM_SOLVE_SCALE=parameters["solve_scale"],
            ICP_SOLVE_SCALE=parameters["solve_scale"],
        )
        config = dataclasses.asdict(codem_run_config)

        fnd_obj, aoi_obj = codem.preprocess(config)
        fnd_obj.prep()
        aoi_obj.prep()
        dsm_reg = codem.coarse_registration(fnd_obj, aoi_obj, config)
        icp_reg = codem.fine_registration(fnd_obj, aoi_obj, dsm_reg, config)
        reg_file = codem.apply_registration(fnd_obj, aoi_obj, icp_reg, config)

        Path(f"{aoi_href}.aux.xml").unlink(missing_ok=True)

        return str(reg_file)

    def create_registered_item(self, registered_path: str) -> Item:
        basepath = Path(registered_path).parent
        registered_item = stactools.core.create.item(registered_path)
        registered_item.assets["data"].title = "Registered AOI"
        registered_item.add_asset(
            key="config",
            asset=Asset(
                href=str(basepath / "config.yml"),
                title="CODEM parameters",
                roles=["metadata"],
            ),
        )
        registered_item.add_asset(
            key="feature_matches",
            asset=Asset(
                href=str(basepath / "dsm_feature_matches.png"),
                title="Coarse registration DSM feature match visual",
                media_type=MediaType.PNG,
                roles=["metadata"],
            ),
        )
        registered_item.add_asset(
            key="registration",
            asset=Asset(
                href=str(basepath / "registration.txt"),
                title="DSM and ICP registration parameters",
                media_type=MediaType.TEXT,
                roles=["metadata"],
            ),
        )
        registered_item.collection_id = "registered"
        registered_item.properties["codem:role"] = "reg"
        return registered_item

    def process(self, **kwargs: Any) -> List[Dict[str, Any]]:
        try:
            assert len(self.items) == 2
            aoi_item = next(
                item
                for item in self.items
                if item.properties.get("codem:role", None) == "aoi"
            )
            fnd_item = next(
                item
                for item in self.items
                if item.properties.get("codem:role", None) == "fnd"
            )
        except (AssertionError, StopIteration) as e:
            raise InvalidInput(
                "Two Items must be provided, one with a 'codem:role' property "
                "equal to 'aoi' and one with a 'codem:role' property equal to 'fnd'"
            ) from e

        aoi_item_down = self.download_item_assets(
            aoi_item, assets=[kwargs["aoi_asset"]]
        )
        aoi_path = aoi_item_down.assets[kwargs["aoi_asset"]].href
        fnd_item_down = self.download_item_assets(
            fnd_item, assets=[kwargs["fnd_asset"]]
        )
        fnd_path = fnd_item_down.assets[kwargs["fnd_asset"]].href

        parameters = {
            arg.replace("codem:", ""): kwargs[arg]
            for arg in kwargs
            if arg.startswith("codem:")
        }
        registered_path = self.run_codem(fnd_path, aoi_path, parameters)

        original_name = Path(Path(aoi_item.assets[kwargs["aoi_asset"]].href).name)
        registered_name = original_name.stem + "-registered" + original_name.suffix
        new_registered_path = Path(registered_path).parent / registered_name
        Path(registered_path).rename(new_registered_path)
        reg_aoi_item = self.create_registered_item(str(new_registered_path))
        reg_aoi_item.add_link(
            Link(rel="derived_from", target=aoi_item.get_single_link(rel="self").target)
        )

        upload_assets = ["data", "config", "feature_matches", "registration"]
        reg_aoi_item_up = self.upload_item_assets_to_s3(reg_aoi_item, upload_assets)

        return [reg_aoi_item_up.to_dict(transform_hrefs=False)]


def main() -> None:
    Coreg.cli()


if __name__ == "__main__":
    main()
