#
# This file contains the original script from the Slicer dev mailing list as to how to
# do the actual plot. It is scratch code and useable from the slicer python interactive
# window. The code in SliceAreaPlot.py is based on it.
#


import vtk.util.numpy_support
import numpy as np

# Volume dimensions
nodeName = 'CTACardio'  #for example file
voxelArray = array(nodeName)
numSlices = np.shape(voxelArray)[0]


segmentationNode = getNode('Segmentation')
segmentId = 'Segment_1'

# Get segment
vimage = segmentationNode.GetBinaryLabelmapRepresentation(segmentId)

# Get extents from segmentation node. The slice number here is the actual
# index into the array of slices, starting with zero.
firstSlice = vimage.GetExtent()[4]
lastSlice = vimage.GetExtent()[5]

# Get segment as numpy array. This results in one big one-dimensional array, in order, of all
# voxel values.
narray = vtk.util.numpy_support.vtk_to_numpy(vimage.GetPointData().GetScalars())
vshape = vimage.GetDimensions()

# Reshape the segment volume to have an array of slices. This resuls in a 2-dimensional
# array, where the first index is into each slice and the second index is basically
# a one-d array that contains all voxel data for that slice. 
#narrayBySlice = narray.reshape([-1,vshape[1]*vshape[2]])
narrayBySlice = narray.reshape([-1,vshape[0]*vshape[1]])

# Count number of >0 voxels for each slice
narrayBySlicePositive = narrayBySlice[:]>0
areaBySliceInVoxels = np.count_nonzero(narrayBySlicePositive, axis=1)

# Convert number of voxels to area in mm2
areaOfPixelMm2 = vimage.GetSpacing()[0] * vimage.GetSpacing()[1]
areaBySliceInMm2 = areaBySliceInVoxels * areaOfPixelMm2

# Insert number of empty slices into front of array and back of array so that
# array is whole extent of data
numFrontSlices = firstSlice - 1
numBackSlices = numSlices - lastSlice
areaBySliceInMm2 = np.insert(areaBySliceInMm2, np.zeros(numFrontSlices,), 0)
areaBySliceInMm2 = np.append(areaBySliceInMm2, np.zeros(numBackSlices))

# Save results to a new table node
tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Segment quantification")
updateTableFromArray(tableNode, areaBySliceInMm2)
tableNode.GetTable().GetColumn(0).SetName("Segment Area")

plotDataNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotDataNode")
plotDataNode.SetAndObserveTableNodeID(tableNode.GetID())
plotDataNode.SetXColumnName("Indexes")
plotDataNode.SetYColumnName(tableNode.GetTable().GetColumn(0).GetName())

plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
plotChartNode.AddAndObservePlotDataNodeID(plotDataNode.GetID())

layoutManager = slicer.app.layoutManager()
layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpPlotView)
plotWidget = layoutManager.plotWidget(0)

plotViewNode = plotWidget.mrmlPlotViewNode()
plotViewNode.SetPlotChartNodeID(plotChartNode.GetID())

