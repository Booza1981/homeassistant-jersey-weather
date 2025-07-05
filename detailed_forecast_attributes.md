# Detailed Forecast Attributes Design

This document outlines the design for the detailed, period-based forecast attributes provided by the Jersey Weather integration.

## Attribute Naming Convention

The attributes follow a consistent naming convention to ensure clarity and ease of use:

`forecast_day_[N]_[period]_[metric]`

-   `[N]`: The forecast day, from 1 to 5.
-   `[period]`: The time of day, which can be `morning`, `afternoon`, or `night`.
-   `[metric]`: The weather metric being measured, such as `temperature`, `condition`, or `rain_probability`.

## Detailed Attribute Structure

Below is the complete structure for the detailed forecast attributes for each of the five forecast days.

### Day 1 Forecast

-   `forecast_day_1_morning_condition`
-   `forecast_day_1_morning_rain_probability`
-   `forecast_day_1_morning_temperature`
-   `forecast_day_1_afternoon_condition`
-   `forecast_day_1_afternoon_rain_probability`
-   `forecast_day_1_afternoon_temperature`
-   `forecast_day_1_night_condition`
-   `forecast_day_1_night_rain_probability`
-   `forecast_day_1_night_temperature`

### Day 2 Forecast

-   `forecast_day_2_morning_condition`
-   `forecast_day_2_morning_rain_probability`
-   `forecast_day_2_morning_temperature`
-   `forecast_day_2_afternoon_condition`
-   `forecast_day_2_afternoon_rain_probability`
-   `forecast_day_2_afternoon_temperature`
-   `forecast_day_2_night_condition`
-   `forecast_day_2_night_rain_probability`
-   `forecast_day_2_night_temperature`

### Day 3 Forecast

-   `forecast_day_3_morning_condition`
-   `forecast_day_3_morning_rain_probability`
-   `forecast_day_3_morning_temperature`
-   `forecast_day_3_afternoon_condition`
-   `forecast_day_3_afternoon_rain_probability`
-   `forecast_day_3_afternoon_temperature`
-   `forecast_day_3_night_condition`
-   `forecast_day_3_night_rain_probability`
-   `forecast_day_3_night_temperature`

### Day 4 Forecast

-   `forecast_day_4_morning_condition`
-   `forecast_day_4_morning_rain_probability`
-   `forecast_day_4_morning_temperature`
-   `forecast_day_4_afternoon_condition`
-   `forecast_day_4_afternoon_rain_probability`
-   `forecast_day_4_afternoon_temperature`
-   `forecast_day_4_night_condition`
-   `forecast_day_4_night_rain_probability`
-   `forecast_day_4_night_temperature`

### Day 5 Forecast

-   `forecast_day_5_morning_condition`
-   `forecast_day_5_morning_rain_probability`
-   `forecast_day_5_morning_temperature`
-   `forecast_day_5_afternoon_condition`
-   `forecast_day_5_afternoon_rain_probability`
-   `forecast_day_5_afternoon_temperature`
-   `forecast_day_5_night_condition`
-   `forecast_day_5_night_rain_probability`
-   `forecast_day_5_night_temperature`

## Data Mapping and Sources

The data for these attributes is sourced from the `jerseyForecast.json` API endpoint. The mapping from the API fields to the Home Assistant attributes is as follows:

| Attribute                               | API Field              |
| --------------------------------------- | ---------------------- |
| `..._morning_condition`                 | `morningDescripiton`   |
| `..._morning_rain_probability`          | `rainProbMorning`      |
| `..._morning_temperature`               | `morningTemp`          |
| `..._afternoon_condition`               | `afternoonDescripiton` |
| `..._afternoon_rain_probability`        | `rainProbAfternoon`    |
| `..._afternoon_temperature`             | `maxTemp`              |
| `..._night_condition`                   | `nightDescripiton`     |
| `..._night_rain_probability`            | `rainProbEvening`      |
| `..._night_temperature`                 | `minTemp`              |
