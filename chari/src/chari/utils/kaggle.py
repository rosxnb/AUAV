from pathlib import Path
import json
import base64
import urllib.request as request
import zipfile
import shutil
import tempfile


def get_config_path(path: Path) -> Path:
    path = path.expanduser()
    return path


def get_credentials(path: Path) -> tuple[str, str]:
    with open(path) as kaggleconf:
        config = json.load(kaggleconf)

    username = config["username"]
    key = config["key"]
    return (username, key)


class __KaggleDownloader:
    def __init__( self, *, config_path: Path = Path("~/.kaggle/kaggle.json")):
        self.base_url = "https://www.kaggle.com/api/v1/datasets/download"
        self.config_path = config_path
        self.__load_creds()
        self.cache : dict[str, str] = dict()
        self.last_download_path = ""

    def __load_creds(self):
        path = get_config_path(self.config_path)
        if not path.exists():
            raise ValueError(f"A valid config_path must be passed to setup KaggleDownloader. \
                             \nCurrent invalid config_path: {self.config_path}")

        creds = get_credentials(path)
        self.username = creds[0]
        self.key = creds[1]

        self.token = base64.b64encode(f"{self.username}:{self.key}".encode()).decode()
        self.headers = {"Authorization": f"Basic {self.token}"}

    def reload_creds(self, path: Path):
        self.config_path = path
        self.__load_creds()

    def download_dataset(
        self,
        *,
        owner: str,
        dataset: str,
        output_folder: Path = Path(),
        output_file: str | None = None,
        force: bool = False
    ) -> Path:
        od = f"{owner}/{dataset}"
        if od in self.cache and not force:
            print(f"{od} was already downloaded, skipping this download call")
            return self.cache[od]

        if not output_file:
            output_file = od

        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        output = output_folder / f"{output_file}.zip"

        download_url = f"{self.base_url}/{owner}/{dataset}"
        req = request.Request(url=download_url, headers=self.headers)

        print(f"downloading {od}...")

        with (request.urlopen(req) as resp,
              open(output, "wb") as out):
            out.write(resp.read())

        self.cache[od] = str(output)
        self.last_download_path = output
        print(f"Downloaded {owner}/{dataset} into {output}")
        return output

    def get_cache(self, owner: str, dataset: str) -> str:
        return self.cache[f"{owner}/{dataset}"]

    def extract_last_download(self):
        self.extract(self.last_download_path)

    def extract(self, path: Path, output_dir: Path = Path()):
        print(f"extracting zipped contents from {path}")
        with zipfile.ZipFile(path) as z:
            z.extractall(output_dir)
        print(f"extracted zipped contents into {output_dir}")

    def extract(self, path: Path, output_dir: Path | None = None) -> Path:
        path = Path(path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"No zip file found at {path}")

        parent = Path(output_dir).expanduser() if output_dir else path.parent
        parent.mkdir(parents=True, exist_ok=True)

        name = path.stem if path.suffix.lower() == ".zip" else path.name
        final = parent / name

        if final.exists() and not final.is_dir() and final != path:
            raise FileExistsError(f"{final} exists and is not a folder")

        print(f"extracting {path} into {final}")

        # extract into a temp folder first, so the zip itself can safely
        # share its name with the final folder (e.g. "abc/file_a")
        tmp = Path(tempfile.mkdtemp(dir=path.parent, prefix=".extract_"))
        try:
            with zipfile.ZipFile(path) as z:
                z.extractall(tmp)

            # if the zip has one top-level folder, use its contents directly
            entries = list(tmp.iterdir())
            content = entries[0] if len(entries) == 1 and entries[0].is_dir() else tmp

            if final == path:
                path.unlink()           # zip is replaced by the extracted folder
            elif final.is_dir():
                shutil.rmtree(final)    # fresh extraction replaces old one

            content.rename(final)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        print(f"extracted into {final}")
        return final

kaggleDownloader = __KaggleDownloader()
