d = open("databooths.txt", "r")
data = d.read()
data_list = data.split("\n")
geojson = open("booths.txt", "w")

# geojson.write("{\n 'features' : [\n")
for i in data_list:
    print(i)
    if i.find("description: ") > -1:
        clubname = i[
            i.find(">") : i.find("<", __start=i.find(">"))
        ]  # if you get any issues, remove __start
        geojson.write("clubname: " + clubname)
        geojson.write(
            'description: "<strong>'
            + clubname
            + '</strong><p><a href="https://maclyonsden.com/club/INSERT" target="_blank" title="Opens in a new window">Club Page</a></p>",'
        )
    elif i.find("icon:") > -1:
        geojson.write('icon: "embassy",')
    else:
        geojson.write(i)

    geojson.write("\n")
    # featuresList = {}
    # line = i[1:len(i)-1].split(",")
    # for x in line:
    #     k,v = x.strip().split(":")
    #     featuresList[k.strip()] = v.strip()
    #     print("feature: "+k.strip()+" "+featuresList[k.strip()])
    # print(i)
    # geojson.write("{\n\t'type': 'Feature',\n\t'geometry':{\n\t\t'type':'Point',\n\t\t'coordinates': ["+featuresList['longitude'][0:-1]+", "+ featuresList['latitude']+"]\n\t},\n\t'properties':{\n\t\t'id':"+featuresList['id']+",\n\t\t'title':"+featuresList['room']+",\n\t\t'floor':"+featuresList['floor']+"\n\t}\n},\n")

# geojson.write("],\n'type': 'FeatureCollection'\n}")

# i.find("description: ")>-1:
#         clubname = i[i.find(">"):i.find(i.find("<"), beg=i.find(">"))]
#         geojson.write("description: \"<strong>"+clubname+"</strong><p><a href=\"\" target=\"_blank\" title=\"Opens in a new window\">Club Page</a></p>\",")
#     elif
