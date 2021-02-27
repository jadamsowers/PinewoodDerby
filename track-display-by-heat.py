import cv2, time, csv, glob, numpy

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

csvFiles = glob.glob('Results/*.csv')
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
    i = 0
    for key, value in heats.items():
        heats_list.append( [ int(value['lane1']), int(value['lane2']), int(value['lane3']) ] )
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

    normalfontpath       = "Fonts/EurostileBold.ttf"
    normalfont           = ImageFont.truetype(normalfontpath, text_size)

    # Set up video file container
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video  = cv2.VideoWriter('Output/' + file[:-4] + '-heats.mov', fourcc, float(FPS), (width, height))

    # pre-render the base image. We will combine it with the live data later.
    base      = Image.fromarray(canvas)
    draw_base = ImageDraw.Draw(base)

    y = 0
    for key, value in cars.items():
        # print car # and name
        draw_base.text((600,  yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = dimcolor_time)
        draw_base.text((900,  yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = dimcolor_time)
        draw_base.text((1200, yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = dimcolor_time)
        draw_base.text((1500, yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = dimcolor_avg)
        y += 1

    #base = ImageChops.screen(base, base.filter(ImageFilter.GaussianBlur(radius=blur_radius)))

    y = 0
    for key, value in cars.items():
        # print car # and name
        draw_base.text((100,  yspacing * (y + 2)), str(key),      font = normalfont,       fill = "#ffffff")
        draw_base.text((200,  yspacing * (y + 2)), value['name'], font = normalfont,       fill = "#ffffff")
        y += 1

    # draw in header information
    draw_base.text((100,  yspacing), '#',           font = italicfont,       fill = "#888888")
    draw_base.text((200,  yspacing), 'Driver',      font = italicfont,       fill = "#888888")
    draw_base.text((600,  yspacing), 'Lane 1',      font = italicfont,       fill = "#888888")
    draw_base.text((900,  yspacing), 'Lane 2',      font = italicfont,       fill = "#888888")
    draw_base.text((1200, yspacing), 'Lane 3',      font = italicfont,       fill = "#888888")
    draw_base.text((1500, yspacing), 'Average',     font = italicfont,       fill = "#888888")

    canvas = numpy.array(base)
    video.write(canvas)




    for i in heats_list:

        # Iterate over each frame
        for f in range(int(FPS * seconds)):

            # convert from CV array to PIL frame
            frame = Image.fromarray(canvas)
            draw  = ImageDraw.Draw(frame)

            elapsed_seconds = f / FPS
                
            # maintain either the elapsed time or the lane time if it has already passed
            l0 = float(cars[i[0]]['lane1time'])
            l1 = float(cars[i[1]]['lane2time'])
            l2 = float(cars[i[2]]['lane3time'])

            val0 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < l0 else l0) )
            val1 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < l1 else l1) )
            val2 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < l2 else l2) )

            y0 = cars_list.index(i[0])
            y1 = cars_list.index(i[1])
            y2 = cars_list.index(i[2])

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
             
            draw.text((600,  yspacing * (y0 + 2)),  val0,         font = sevensegmentfont, fill = regcolor_time)
            draw.text((900,  yspacing * (y1 + 2)),  val1,         font = sevensegmentfont, fill = regcolor_time)
            draw.text((1200, yspacing * (y2 + 2)),  val2,         font = sevensegmentfont, fill = regcolor_time)
            #draw.text((1500, yspacing * (y + 2)),  "-.---",      font = sevensegmentfont, fill = regcolor_avg)

            # write the frame to disk
            video.write(numpy.array(frame))
        
        canvas = numpy.array(frame)

    for a in range(len(cars_list)):
        average = str('{0:.3f}'.format(cars[cars_list[a]]['average']))

        frame = Image.fromarray(canvas)
        draw  = ImageDraw.Draw(frame)
        draw.text((1500, yspacing * (a + 2)), average, font = sevensegmentfont, fill = regcolor_avg)
        frame_array = numpy.array(frame)
        video.write(frame_array)
        canvas = frame_array

    frame = Image.fromarray(canvas)
    draw  = ImageDraw.Draw(frame)
    for key, value in advancers.items():
        draw.text((600,  yspacing * (cars_list.index(key) + 2)), '{0:.3f}'.format(float(cars[key]['lane1time'])), font = sevensegmentfont, fill = regcolor_adv)
        draw.text((900,  yspacing * (cars_list.index(key) + 2)), '{0:.3f}'.format(float(cars[key]['lane2time'])), font = sevensegmentfont, fill = regcolor_adv)
        draw.text((1200, yspacing * (cars_list.index(key) + 2)), '{0:.3f}'.format(float(cars[key]['lane3time'])), font = sevensegmentfont, fill = regcolor_adv)
        draw.text((1500, yspacing * (cars_list.index(key) + 2)), '{0:.3f}'.format(cars[key]['average']),          font = sevensegmentfont, fill = regcolor_adv)
    
    frame_array = numpy.array(frame)
    for r in range(FPS * 3):
        video.write(frame_array)