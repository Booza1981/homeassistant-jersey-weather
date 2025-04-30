# Jersey Weather Integration Roadmap

This document outlines planned improvements for the Jersey Weather Home Assistant integration.

## 1. Enhanced Tide Handling

**Current Issue:** 
- Tide information is difficult to read and interpret
- Individual tide sensors (1-4) don't provide a clear picture of tide patterns

**Proposed Solution:**
- Implement a more visual tide representation similar to the approach in [this community thread](https://community.home-assistant.io/t/tides-in-lovelace/337659/61)
- Create a single tide entity with attributes for all tide events
- Consider adding a tide chart visualization option
- Include time until next high/low tide as an attribute
- Provide tide height as a percentage of max/min (more intuitive than absolute values)

**Technical Approach:**
- Process tide data to calculate time until next event
- Store tide events as structured data for better representation
- Consider implementing a custom card for tide visualization

## 2. Improved Weather Image Handling

**Current Issue:**
- Weather images (radar, satellite, sea state) show as "Idle" when not actively refreshing
- No context is provided about the images
- Users can't view historical images

**Proposed Solution:**
- Enable scrolling through multiple images for each camera entity
- Add timestamp information to each image
- Include descriptions of what each image represents
- Replace "Idle" with meaningful status information

**Technical Approach:**
- Modify camera.py to support multiple images per camera
- Add image metadata including timestamps and descriptions
- Store historical images (with reasonable limits)
- Enhance the camera entity to expose this additional information

## 3. Live Weather Observations Integration

**Current Issue:**
- Missing valuable real-time data from the live observations page
- No humidity data in current integration
- Air pressure only available from coastal reports (not real-time)

**Proposed Solution:**
- Add data scraping from the [Live Weather Observations page](https://www.gov.je/weather/liveweatherobservations/)
- Implement new sensors for:
  - Live temperature (more frequently updated)
  - Humidity
  - Real-time air pressure
  - Other available metrics from this source

**Technical Approach:**
- Create a new data source in the coordinator
- Add image processing capability to extract data from weather station images
- Reuse existing python script for extracting temperature from images
- Add additional image processing for other metrics

## 4. Moon Phase Information

**Current Issue:**
- No moon phase information available in the integration
- Moon phases are relevant for tide and outdoor activities

**Proposed Solution:**
- Add a moon phase sensor showing current phase
- Include percentage of moon illumination
- Add moon rise/set times
- Include next full/new moon date as attributes

**Technical Approach:**
- Calculate moon phase using astronomical algorithms
- Add a new sensor class for moon information
- Use the appropriate icon set to visually represent the moon phase
- Consider local Jersey coordinates for accurate rise/set times

## 5. General UX Improvements

**Current Issue:**
- Some data representations could be more intuitive
- Limited dashboard integration examples

**Proposed Solution:**
- Add more pre-configured dashboard examples
- Improve icon selection for better visual clarity
- Ensure all entities have appropriate units and device classes
- Add historical data viewing where applicable

**Technical Approach:**
- Update the README with comprehensive dashboard examples
- Review and standardize all entity representations
- Consider custom cards for specialized data views

## Implementation Priority

1. Enhanced Tide Handling (Highest priority based on user feedback)
2. Live Weather Observations Integration
3. Improved Weather Image Handling
4. Moon Phase Information
5. General UX Improvements

## Timeline

This is a community project with no fixed timeline, but these features will be tackled based on priority and contributor availability.

## Contributing

Contributions to any of these enhancements are welcome! Please submit pull requests or open issues on the GitHub repository to discuss implementation details.
