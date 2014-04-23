SELECT 'id', 'name'
UNION ALL
SELECT EANHotelID, TRIM(CONCAT(REPLACE(Name, '"', ''), ", ", City, ", ", Country))
FROM activepropertylist
INTO OUTFILE '/tmp/property_index.csv'
FIELDS TERMINATED BY '|'
LINES TERMINATED BY '\n';

