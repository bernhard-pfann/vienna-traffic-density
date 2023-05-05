import os


root        = os.environ['HOME']+"/private/vienna-traffic-density/"
root_input  = os.path.join(root, "artifacts", "input")
root_output = os.path.join(root, "artifacts", "output")
root_img    = os.path.join(root, "artifacts", "img")

uber_url_base = "https://movement.uber.com/explore/vienna/travel-times/query"
uber_url_params = {
    "lat.": 48.2082,
    "lng.": 16.3384378,
    "z.": 12,
    "lang": "en-US",
    "si": 360,
    "ti": "",
    "ag": "statistical_areas",
    "dt[tpb]": "ALL_DAY",
    "dt[wd;]": "1,2,3,4,5,6,7",
    "dt[dr][sd]": "2020-03-01",
    "dt[dr][ed]": "2020-03-31",
    "cd": "",
    "sa;": "",
    "sdn": "",
}