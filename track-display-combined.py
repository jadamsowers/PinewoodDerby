import cv2, time, csv, glob, numpy

from PIL         import ImageFont, ImageDraw, Image, ImageFilter, ImageChops
from collections import defaultdict
from operator    import itemgetter

width       = 1920
height      = 1080
FPS         = 60
seconds     = 5

text_size   = 48
blur_radius = 5
yspacing    = 80

dimcolor_time = "#000022"
regcolor_time = "#0000ff"
dimcolor_avg  = "#220000"
regcolor_avg  = "#ff0000"
dimcolor_adv  = "#002200"
regcolor_adv  = "#00ff00"

csvFiles = glob.glob('*.csv')
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

    # coalesce the lane data down by car
    for datum in trackdata:
        car = {}
        if datum['number'] in cars:
            car = cars[datum['number']]
        
        car |= {
            'name': datum['name'],
            'lane' + datum['lane'] + 'time': datum['time']
        }
        cars[datum['number']] = car

    # calculate average times and store fastest 3
    avg_times = {}
    for key, value in cars.items():
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
    r,g,b,a = 255,0,0,0

    # Set up fonts
    sevensegmentfontpath = "Fonts/DSEG7Classic-Italic.ttf"
    sevensegmentfont     = ImageFont.truetype(sevensegmentfontpath, text_size)

    italicfontpath       = "Fonts/EurostileOblique.ttf"
    italicfont           = ImageFont.truetype(italicfontpath, text_size)

    normalfontpath       = "Fonts/EurostileBold.ttf"
    normalfont           = ImageFont.truetype(normalfontpath, text_size)

    # Set up video file container
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    video  = cv2.VideoWriter('Output/' + file[:-4] + '.mov', fourcc, float(FPS), (width, height))

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
        draw_base.text((100,  yspacing * (y + 2)), key,           font = normalfont,       fill = "#ffffff")
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


    # Iterate over each frame
    for f in range(int(FPS * seconds)):

        # convert from CV array to PIL frame
        frame = Image.fromarray(canvas)
        draw  = ImageDraw.Draw(frame)
        
        num_entries = 5

        elapsed_seconds = f / FPS

        y = 0

        for key, value in cars.items():
            
            # maintain either the elapsed time or the lane time if it has already passed
            val1 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < value['lanetimes'][0] else value['lanetimes'][0]))
            val2 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < value['lanetimes'][1] else value['lanetimes'][1]))
            val3 = str( '{0:.3f}'.format(elapsed_seconds if elapsed_seconds < value['lanetimes'][2] else value['lanetimes'][2]))
            max_val = max(value['lanetimes'])

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
            if elapsed_seconds < max_val:
                
                draw.text((600,  yspacing * (y + 2)),  val1,         font = sevensegmentfont, fill = regcolor_time)
                draw.text((900,  yspacing * (y + 2)),  val2,         font = sevensegmentfont, fill = regcolor_time)
                draw.text((1200, yspacing * (y + 2)),  val3,         font = sevensegmentfont, fill = regcolor_time)
                draw.text((1500, yspacing * (y + 2)),  "-.---",      font = sevensegmentfont, fill = regcolor_avg)
            else:
                draw.text((600,  yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = my_dimcolor_time)
                draw.text((600,  yspacing * (y + 2)),  val1,         font = sevensegmentfont, fill = my_regcolor_time)
                draw.text((900,  yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = my_dimcolor_time)
                draw.text((900,  yspacing * (y + 2)),  val2,         font = sevensegmentfont, fill = my_regcolor_time)
                draw.text((1200, yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = my_dimcolor_time)
                draw.text((1200, yspacing * (y + 2)),  val3,         font = sevensegmentfont, fill = my_regcolor_time)
                draw.text((1500, yspacing * (y + 2)),  "8.888",      font = sevensegmentfont, fill = my_dimcolor_avg)
                draw.text((1500, yspacing * (y + 2)),  average,      font = sevensegmentfont, fill = my_regcolor_avg)

            y += 1

        # write the frame to disk
        video.write(numpy.array(frame))

