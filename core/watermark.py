import fitz
from PIL import Image, ImageDraw, ImageFont	
import math
import io

# Function to add watermark to all pages of a pdf.
def addWatermark(doc, imgObj, tilePerRow):
	# Make a Pixmap where the email image is tiled across the whole page.
	pageWatermarkPixmap = tileImageToPage(imgObj, doc[0], tilePerRow)
	
	# Iterate through the entire pdf document.
	for page in doc:
		# Code to set the page settings/attributes.
		page._cleanContents()	
		# Add the tiled watermark pixmap to the page.
		page.insertImage(page.rect, pixmap = pageWatermarkPixmap, keep_proportion=True)
	
	return doc
	
# Function to tile email image that spans the whole page of a pdf.
def tileImageToPage(imgObj, page, tilePerRow): 
	pageWidth = int(page.MediaBoxSize.x)
	pageHeight = int(page.MediaBoxSize.y)
	
	# Generates size of an image tile based on the dimensions 
	# of a page and the number of tiles per row.
	tileWidth, tileHeight = getTileSize(pageWidth, pageHeight, tilePerRow, imgObj)
	
	# Make a pixmap for the tile.
	tileImg = resizeImageToTilePixmap(imgObj, tileWidth, tileHeight)
	
	# Make a pixmap to place the tiled image on.
	pagePic = fitz.Pixmap(fitz.csRGB, page.rect.irect, tileImg.alpha)
	
	# Iterate per tile row
	for i in range(int(pageHeight/tileHeight)):
		# Set Tile pixmap Y coordinate
		tileImg.y = i * tileImg.height
		for j in range(int(pageWidth/tileWidth)):
			# Set Tile pixmap X coordinate
			tileImg.x = j * tileImg.width
			# Place Tile pixmap on the Page pixmap
			pagePic.copyPixmap(tileImg, tileImg.irect)
			
	#pagePic.writePNG("wholePageWM2.png")
	return pagePic
	
	
# Function for generating tile size. Returns tile height and width
def getTileSize(pageWidth, pageHeight, tilePerRow, imgObj):
	# Get ratio percentage for page width:tile width for keeping aspect ratio of email image
	wpercent = (pageWidth/tilePerRow)/float(imgObj.width)
	# Compute tile height based on wpercent to keep aspect ratio of email image
	hsize = int((float(imgObj.height)*float(wpercent)))
	return int(pageWidth/tilePerRow), hsize
	
	
#Resize image to tile size. Returns a pixmap of the tiled image.
def resizeImageToTilePixmap(imgObj, tileWidth, tileHeight):
	# Change 4 to 3 for speed at the cost of quality
	imgResized = imgObj.resize((int(tileWidth), int(tileHeight)),  3)
	
	# For turning the Image object into a BytesIO in order to convert to Pixmap
	buffer = io.BytesIO()
	imgResized.save(buffer, format="PNG")
	
	return fitz.Pixmap(buffer.getvalue())

# Utility function for makeEmailImage
def getEmailImageSize(txt, font):
    testImg = Image.new('RGB', (1, 1))
    testDraw = ImageDraw.Draw(testImg)
    return testDraw.textsize(txt, font)
	
# Function that returns a PIL Image object for email text image.
def makeEmailImage(text, fontname, fontsize, fontfill):
	# Make Font object
	fnt = ImageFont.truetype(fontname, fontsize)
	# Generate size of resulting  image
	size = getEmailImageSize(text, fnt)
	# Make a new Image object with alpha layer
	img = Image.new('RGBA', size, (255,255,255,0))
	# Draw Image
	d = ImageDraw.Draw(img)
	# Add text to Image
	d.text((0,0), text, fill=fontfill, font=fnt)
	# Return Image rotated by 60 degrees
	return img.rotate(60, resample=Image.BILINEAR, expand=True)
	
# Main runtime function
def mainRuntime(email, pdf):
	# Supply variables to make email text image.
	text = email 					# This is one of the two inputs.
	fontname = "arial.ttf"
	fontsize = 40
	fontfill = (0,0,0,63) 			# Black font color with 25% transparency.
	
	# Step 1: Make Email text image.
	imgObj = makeEmailImage(text, fontname, fontsize, fontfill)
	
	# Supply variables to make PDF.
	inputPdf = pdf					# This is the second of the two inputs.
	tilesPerRow = 10				# This is the number of times the email 
									# will be printed in a row. Can be changed. 
									# I think it affects run time haven't tested yet.
	
	# Open document using PyMuPDF.
	doc = fitz.open(inputPdf)
	
	# Step 2: Add watermark to pdf.
	newDoc = addWatermark(doc, imgObj, tilesPerRow)
	
	# Save file while compressing the objects in the pdf.
	newDoc.save("watermarked_output.pdf", garbage=3, deflate=True)


if __name__ == '__main__':
	# The following is for timing n number of execusions.
	# Change the value of n as needed.
	n = 1
	
	# pageNumber is the number of pages in the pdf. Manual muna sorry haha
	pageNumber = 9
	
	import timeit
	executionTime = timeit.timeit("mainRuntime()", 
		setup="from __main__ import mainRuntime, " +
			"resizeImageToTilePixmap, getTileSize, " +
			"tileImageToPage, addWatermark, " +
			"getEmailImageSize, makeEmailImage",
		number=n)
	print(f"Execution time for {n} execusions: {executionTime}s")
	print(f"Average Execution time per {n} page document: {executionTime/float(n)}s")
	print(f"Average Execution time per page: {((executionTime/float(n))/pageNumber)*1000}ms")