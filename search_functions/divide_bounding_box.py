def divide_bounding_box(bounds, divisions):
    """
    Divide a bounding box into smaller boxes.
    """
    lat_step = (bounds['northeast']['lat'] - bounds['southwest']['lat']) / divisions
    lng_step = (bounds['northeast']['lng'] - bounds['southwest']['lng']) / divisions
    
    sub_boxes = []
    for i in range(divisions):
        for j in range(divisions):
            sub_box = {
                'southwest': {
                    'lat': bounds['southwest']['lat'] + i * lat_step,
                    'lng': bounds['southwest']['lng'] + j * lng_step
                },
                'northeast': {
                    'lat': bounds['southwest']['lat'] + (i + 1) * lat_step,
                    'lng': bounds['southwest']['lng'] + (j + 1) * lng_step
                }
            }
            sub_boxes.append(sub_box)
    
    return sub_boxes