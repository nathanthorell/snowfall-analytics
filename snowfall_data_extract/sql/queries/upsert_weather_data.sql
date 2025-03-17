INSERT OR REPLACE INTO weather_data (
    station_id,
    date,
    precipitation,
    precipitation_attributes,
    snowfall,
    snowfall_attributes,
    snow_depth,
    snow_depth_attributes,
    temp_max,
    temp_max_attributes,
    temp_min,
    temp_min_attributes
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
