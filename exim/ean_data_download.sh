#!/bin/bash

cookie_file="../out/ean_cookie.txt"
base_download_url="https://www.ian.com/affiliatecenter/include/V2/"
download_dir="../ean_data/new/"
FILES="ActivePropertyList.zip
AttributeList.zip
PropertyAttributeLink.zip
HotelImageList.zip
ParentRegionList.zip
CityCoordinatesList.zip
AirportCoordinatesList.zip
NeighborhoodCoordinatesList.zip
PointsofInterestCoordinatesList.zip
RegionCenterCoordinatesList.zip
RegionEANHotelIDMapping.zip"

echo "[1] Downloading files from EAN"

echo "Logging in"
curl -c $cookie_file --silent -X POST -d "handle":"rextrebat","passwd":"eanlara375","process":"Sign In" https://developer.ean.com/login/login > /dev/null

for file in $FILES
do
    echo "Downloading $file"
    curl -b $cookie_file --silent --output $download_dir$file $base_download_url$file
done

echo "[2] Unzipping files"
unzip $download_dir"*.zip" 1>/dev/null

echo "[3] Loading data into tables"

echo "[4] Running gene tagger"

echo "[5] Running chromosome tagger"

echo "Done"
