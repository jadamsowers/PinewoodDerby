import cv2, time, csv, glob, numpy, re

from PIL         import ImageFont, ImageDraw, Image, ImageFilter, ImageChops
from collections import defaultdict
from operator    import itemgetter

width       = 1920
height      = 1080
FPS         = 60
seconds     = 3.5

text_size   = 48
blur_radius = 5
yspacing    = 80

dimcolor_time = "#000022"
regcolor_time = "#0000ff"
dimcolor_avg  = "#220000"
regcolor_avg  = "#ff0000"
dimcolor_adv  = "#002200"
regcolor_adv  = "#00ff00"

csvFiles = glob.glob('Results/RaceResultsFinal.csv')
for file in csvFiles:

    trackdata = []
    cars = defaultdict(dict)

    # import the CSV file data and convert to a usable format
    with open(file) as csvfile:
        print('processing ' + file)
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            trackdata.append({
                'number': row['Car#'],
                'name':   row['First Name'] + ' ' + row['Last Name'][0] + '.',
                'lane':   row['Lane'],
                'time':   row['Time'],
                'mph':    row['Avg MPH'],
                'heat':   row['Master\nHeat#']
            })

    # coalesce the lane data by car
    for datum in trackdata:
        car = {}
        num = int(datum['number'])
        if num in cars:
            car = cars[num]
        
        car |= {
            'name': datum['name'],
            'lane' + datum['lane'] + 'time': datum['time']
        }
        cars[num] = car

    # coalesce the lane data by heat
    heats = defaultdict(dict)
    for datum in trackdata:
        heat = {}
        if datum['heat'] in heats:
            heat = heats[datum['heat']]

        heat |= {
            'lane' + datum['lane']: datum['number']
        }
        heats[datum['heat']] = heat

    heats_list = []
    sorted_heats = sorted(heats.keys(), key=lambda x:int(x))
    i = 0
    for heat in sorted_heats:
        heat_item = heats[heat]
        heats_list.append( [ int(heat_item['lane1']), int(heat_item['lane2']), int(heat_item['lane3']) ] )
        i += 1
    
    # calculate average times and store fastest 3
    avg_times = {}
    cars_list = []
    i = 0
    for key, value in cars.items():
        cars_list.append(int(key))
        i += 1
        lanetimes = [ float(value['lane1time']), float(value['lane2time']), float(value['lane3time']) ]
        avg = numpy.average(lanetimes)
        cars[key] |= {
            'lanetimes': lanetimes,   
            'average':   avg
        }
        avg_times[key] = avg
        advancers = dict(sorted(avg_times.items(), key = itemgetter(1))[:3])


    # Make canvas and set the color
    canvas  = numpy.zeros((height,width,3),numpy.uint8)

    # Set up fonts
    sevensegmentfontpath = "Fonts/DSEG7Classic-Italic.ttf"
    sevensegmentfont     = ImageFont.truetype(sevensegmentfontpath, text_size)

    italicfontpath       = "Fonts/EurostileOblique.ttf"
    italicfont           = ImageFont.truetype(italicfontpath, text_size)
    bigitalicfont        = ImageFont.truetype(italicfontpath, int(text_size * 2.5))

    normalfontpath       = "Fonts/EurostileBold.ttf"
    normalfont           = ImageFont.truetype(normalfontpath, text_size)

    # Set up video file container
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video  = cv2.VideoWriter('Output/' + re.sub(r'^Results\/(.*)\.csv$', r'\1', file) + '-heats.mov', fourcc, float(FPS), (width, height))

    # pre-render the base image. We will combine it with the live data later.
    base      = Image.fromarray(canvas)
    draw_base = ImageDraw.Draw(base)

    y = 0
    for i in range(len(heats_list[0])):

        draw_base.text((600,  yspacing * (y + 4)),  "8.888",      font = sevensegmentfont, fill = dimcolor_time)
        draw_base.text((900,  yspacing * (y + 4)),  "8.888",      font = sevensegmentfont, fill = dimcolor_time)
        draw_base.text((1200, yspacing * (y + 4)),  "8.888",      font = sevensegmentfont, fill = dimcolor_time)
        #raw_base.text((1500, yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = dimcolor_avg)
        y += 1

    # draw in header information
    
    draw_base.text((100,  yspacing * 3), '#',           font = italicfont,       fill = "#888888")
    draw_base.text((200,  yspacing * 3), 'Driver',      font = italicfont,       fill = "#888888")
    draw_base.text((600,  yspacing * 3), 'Lane 1',      font = italicfont,       fill = "#888888")
    draw_base.text((900,  yspacing * 3), 'Lane 2',      font = italicfont,       fill = "#888888")
    draw_base.text((1200, yspacing * 3), 'Lane 3',      font = italicfont,       fill = "#888888")
    #draw_base.text((1500, yspacing), 'Average',     font = italicfont,       fill = "#888888")

    canvas = numpy.array(base)
    video.write(canvas)



    h = 0
    for heat in heats_list:

        h += 1
        # Iterate over each frame
        for f in range(int(FPS * seconds)):

            # convert from CV array to PIL frame
            frame = Image.fromarray(canvas)
            draw  = ImageDraw.Draw(frame)

            elapsed_seconds = f / FPS
                
            # maintain either the elapsed time or the lane time if it has already passed
            l0 = float(cars[heat[0]]['lane1time'])
            l1 = float(cars[heat[1]]['lane2time'])
            l2 = float(cars[heat[2]]['lane3time'])

            val0 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < l0 else l0) )
            val1 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < l1 else l1) )
            val2 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < l2 else l2) )



            # set color based on whether car will advance to finals or not
            my_dimcolor_time = dimcolor_time
            my_regcolor_time = regcolor_time
            my_dimcolor_avg  = dimcolor_avg
            my_regcolor_avg  = regcolor_avg
            if key in advancers.keys():
                my_dimcolor_time = dimcolor_adv
                my_regcolor_time = regcolor_adv
                my_dimcolor_avg  = dimcolor_adv
                my_regcolor_avg  = regcolor_adv

            average = str('{0:.3f}'.format(value['average']))

            # print times in proper color
            draw.text((450,  yspacing * 1.5), 'Heat #' + str(h),           font = bigitalicfont,    fill = "#888888")
            draw.text((100,  yspacing * (0 + 4)), str(heat[0]),            font = normalfont,       fill = "#FFFFFF")
            draw.text((200,  yspacing * (0 + 4)), cars[heat[0]]['name'],   font = normalfont,       fill = "#FFFFFF")
            draw.text((600,  yspacing * (0 + 4)), val0,                    font = sevensegmentfont, fill = regcolor_time)
            draw.text((100,  yspacing * (1 + 4)), str(heat[1]),            font = normalfont,       fill = "#FFFFFF")
            draw.text((200,  yspacing * (1 + 4)), cars[heat[1]]['name'],   font = normalfont,       fill = "#FFFFFF")
            draw.text((900,  yspacing * (1 + 4)), val1,                    font = sevensegmentfont, fill = regcolor_time)
            draw.text((100,  yspacing * (2 + 4)), str(heat[2]),            font = normalfont,       fill = "#FFFFFF")
            draw.text((200,  yspacing * (2 + 4)), cars[heat[2]]['name'],   font = normalfont,       fill = "#FFFFFF")
            draw.text((1200, yspacing * (2 + 4)), val2,                    font = sevensegmentfont, fill = regcolor_time)
            #draw.text((1500, yspacing * (y + 2)),  "-.---",      font = sevensegmentfont, fill = regcolor_avg)

            # write the frame to disk
            video.write(numpy.array(frame))
        
        #canvas = numpy.array(frame)
    
        frame_array = numpy.array(frame)
        for r in range(FPS * 6):
            video.write(frame_array)