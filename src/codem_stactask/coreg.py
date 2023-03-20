import dataclasses
import shutil
from pathlib import Path
from typing import Any, Dict, List

import codem
import stactools.core.create
from pystac import Asset, Item, MediaType
from stactask import Task


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

        # clean up codem detritus
        Path(f"{aoi_href}.aux.xml").unlink(missing_ok=True)

        return str(reg_file)

    def create_registered_item(self, registered_path: str) -> Item:
        basepath = Path(registered_path).parent
        registered_item = stactools.core.create.item(registered_path)
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
        return registered_item

    def process(self, **kwargs: Any) -> List[Dict[str, Any]]:
        registered_items = []
        for item in self.items:
            # 'download': assets already local
            aoi_href = item.assets[kwargs["asset"]].href
            fnd_href = kwargs["foundation_href"]

            # 'do some stuff': register
            parameters = {"solve_scale": kwargs["solve_scale"]}
            registered_path = self.run_codem(fnd_href, aoi_href, parameters)

            # 'upload': destructively tidy generated assets
            move_to = Path(kwargs["output_href"], Path(registered_path).stem)
            if move_to.is_dir():
                shutil.rmtree(move_to)
            Path(registered_path).parent.rename(move_to)
            registered_path = str(move_to / Path(registered_path).name)

            # item for output payload
            registered_item = self.create_registered_item(registered_path)
            registered_items.append(registered_item.to_dict(transform_hrefs=False))

        return registered_items


def main() -> None:
    Coreg.cli()


if __name__ == "__main__":
    main()
