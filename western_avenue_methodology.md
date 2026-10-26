# Western Avenue Corridor: Boundary Methodology and Results

## 1. Objective
Define and validate a geographic corridor along Western Avenue in Los
Angeles using official road geometry and business-location data.

## 2. Corridor selection
The selected road is Western Avenue, between Wilshire Boulevard and
West 3rd Street. The endpoints are based on the road-network
intersection evidence inspected from the City of Los Angeles street
centerline service.

## 3. Data sources
- City of Los Angeles Street Information road-centerline GIS service.
- City of Los Angeles Listing of Active Businesses dataset.
- Business coordinates and attributes from the locally saved CSV.

## 4. Boundary method
The selected Western Avenue centerline was projected to EPSG:32611,
a metre-based coordinate reference system suitable for this area.
A 100 m buffer was created on each side of the clipped centerline.
Flat end caps were used so the buffer would not extend an extra 100 m
past the selected endpoints.

## 5. Results
- Centerline length: 745.3 metres
- Buffer on each side: 100 metres
- Boundary area: 0.1491 square kilometres
- Business records checked: 251
- Records inside boundary: 246
- Business-record coverage: 98.01%

## 6. Buffer-width comparison
The comparison using the saved centerline produced:

| Buffer each side | Businesses inside | Coverage | Area (km²) |
|---:|---:|---:|---:|
| 50 m | 192/251 | 76.49% | 0.0745 |
| 100 m | 246/251 | 98.01% | 0.1491 |
| 150 m | 248/251 | 98.80% | 0.2236 |
| 200 m | 248/251 | 98.80% | 0.2981 |

The 100 m buffer is a reasonable provisional choice because it captures
98.01% of the collected business records while keeping the mapped area
smaller than the 150 m and 200 m alternatives. Wider buffers add few
business records in this dataset but increase the area substantially.

## 7. Outside-record inspection
Three outside records near 319–321 S Western Avenue are approximately
9.3 m from the centerline but fall beyond the northern endpoint.
Two records at 450 S Western Avenue are approximately 146.2 m from the
centerline and fall outside the 100 m buffer.

The northern endpoint was checked against official road records.
Western Avenue and West 3rd Street share intersection ID 18879 in the
returned road-network attributes.

## 8. Limitations
1. Business coverage describes the records in the collected dataset; it
   does not prove that every included business belongs to the corridor.
2. Business records can have missing categories or shared coordinates.
   These records should not be removed without checking their source.
3. A 100 m buffer is an analytical choice, not a universally correct
   corridor width. It should also be checked against maps, land use,
   pedestrian access, and the project's intended definition of a corridor.
4. The intersection check supports the endpoint choice, but final
   visual inspection of the saved map and source geometry remains important.
5. This analysis does not yet establish business density, employment,
   population, building density, or independent field validation.

## 9. Conclusion
The current boundary is a reproducible, data-informed proposal for the
Western Avenue segment between Wilshire Boulevard and West 3rd Street.
It follows the selected official road centerline and uses a 100 m buffer
on each side. Business coverage and alternative buffer widths provide
supporting evidence, while geographic context and the intended corridor
definition remain important validation criteria.
