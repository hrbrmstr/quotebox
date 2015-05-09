import argparse
from os.path import basename, splitext
from subprocess import call
from json import load
from urllib import quote
from PIL import Image

# NOTE that everything keys off the filename basename
# i could add options to override that if need be

# read in the solitary (for now) argument which is the config file

parser = argparse.ArgumentParser()
parser.add_argument("config")
args = parser.parse_args()

# read in the config file

with open(args.config) as config_file:    
    opts = load(config_file)

# get logo dimensions

im = Image.open(opts["logo"])

width, height = im.size

# twitter embedded tweet media is 640x360

x = 640 - width - 25
y = 360 - height - 25

# now, fill in SVG bopilerplate

temp = """
<svg width="640px" height="360px" viewBox="0 0 640 360" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">

  <defs>
    <style type="text/css">@import url('http://fonts.googleapis.com/css?family=Lato:300,900');</style>
  </defs>

  <rect width="640px" height="360px" style="fill:white" />

  <foreignObject x="25" y="25" width="590" height="165">
    <body xmlns="http://www.w3.org/1999/xhtml"
      style="background: white; font-family: Lato; font-weight:900; font-stretch:normal; font-size:36px; line-height:36px; text-indent:-16px; margin-left:20px; color:#333333">
      <p>&#8220;%s&#8221;</p>
    </body>
  </foreignObject>

  <foreignObject x="40" y="200" width="540" height="165">
    <body xmlns="http://www.w3.org/1999/xhtml"
      style="background: white; font-family: Lato; font-weight:300; font-stretch:normal; font-size:20px; line-height:20px; color:#333333">
      <p>&#8212; %s</p>
    </body>
  </foreignObject>

  <image xlink:href="data:image/png;base64,%s" x="%d" y="%d" height="%dpx" width="%dpx"/>

</svg>
""" % (opts["quote"], opts["source"], quote(open(opts["logo"], "rb").read().encode("base64")), x, y, height, width)

# write out SVG file

out_svg = splitext(basename(args.config))[0] + ".svg"

with open(out_svg, "w") as svg_file:
    svg_file.write(temp.encode('utf8'))

# don't rely on rasterize.js to be anywhere on the system
# so embed it here and write it out to /tmp (yeah yeah i know)

rast = """
var page = require('webpage').create(),
    system = require('system'),
    address, output, size;

if (system.args.length < 3 || system.args.length > 5) {
    console.log('Usage: rasterize.js URL filename [paperwidth*paperheight|paperformat] [zoom]');
    console.log('  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"');
    console.log('  image (png/jpg output) examples: "1920px" entire page, window width 1920px');
    console.log('                                   "800px*600px" window, clipped to 800x600');
    phantom.exit(1);
} else {
    address = system.args[1];
    output = system.args[2];
    page.viewportSize = { width: 600, height: 600 };
    if (system.args.length > 3 && system.args[2].substr(-4) === ".pdf") {
        size = system.args[3].split('*');
        page.paperSize = size.length === 2 ? { width: size[0], height: size[1], margin: '0px' }
                                           : { format: system.args[3], orientation: 'portrait', margin: '1cm' };
    } else if (system.args.length > 3 && system.args[3].substr(-2) === "px") {
        size = system.args[3].split('*');
        if (size.length === 2) {
            pageWidth = parseInt(size[0], 10);
            pageHeight = parseInt(size[1], 10);
            page.viewportSize = { width: pageWidth, height: pageHeight };
            page.clipRect = { top: 0, left: 0, width: pageWidth, height: pageHeight };
        } else {
            console.log("size:", system.args[3]);
            pageWidth = parseInt(system.args[3], 10);
            pageHeight = parseInt(pageWidth * 3/4, 10); // it's as good an assumption as any
            console.log ("pageHeight:",pageHeight);
            page.viewportSize = { width: pageWidth, height: pageHeight };
        }
    }
    if (system.args.length > 4) {
        page.zoomFactor = system.args[4];
    }
    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('Unable to load the address!');
            phantom.exit(1);
        } else {
            window.setTimeout(function () {
                page.render(output);
                phantom.exit();
            }, 200);
        }
    });
}
"""

with open("/tmp/rasterize.js", "w") as rast_file:
    rast_file.write(rast.encode('utf8'))

# call phantomjs (>=2.0) to rasterize the svg

out_png = splitext(basename(args.config))[0] + ".png"

call(["phantomjs", "/tmp/rasterize.js", out_svg, out_png, "640px*360px"])

