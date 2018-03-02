cmake_minimum_required(VERSION 3.5)

project(AMNHCTTools)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/AMNHCTTools")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Hollister Herhold (AMNH)")
set(EXTENSION_DESCRIPTION "Various tools for CT analysis at AMNH.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/AMNHCTTools.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/AMNHCTTools/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SliceAreaPlot)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
