def download_airsim():
    from chari.utils.common import does_path_exits
    if does_path_exits("data/luikepellant_airsim"):
        print("airsim data alredy downloaded")
        return

    from chari.utils.kaggle import kaggleDownloader as kgd
    kgd.download_dataset(owner="lukpellant",
                         dataset="droneflight-obs-avoidanceairsimrgbdepth10k-320x320",
                         output_folder="test_data",
                         output_file="luikepellant_airsim")
    kgd.extract_last_download()


def main():
    download_airsim()


if __name__ == "__main__":
    main()
