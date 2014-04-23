SELECT 'id', 'name', 'type'
UNION ALL
SELECT RegionID, RegionNameLong, RegionType
FROM parentregionlist
WHERE RegionType IN ('City', 'Multi-City (Vicinity)', 'Neighborhood', 'Point of Interest Shadow')
INTO OUTFILE '/tmp/region_index.csv'
FIELDS TERMINATED BY '|'
LINES TERMINATED BY '\n';

