import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from array import array
import logging
import vtk.util.numpy_support
import numpy as np

#
# SliceAreaPlot
#

class SliceAreaPlot(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Slice Area Plot" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Quantification"]
    self.parent.dependencies = []
    self.parent.contributors = ["Hollister Herhold (AMNH)"] 
    self.parent.helpText = """
This module computes the cross sectional area of a segment and plots it along the length of the segment.
(Initially. It should eventually do length, width, and breadth.)
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# SliceAreaPlotWidget
#

class SliceAreaPlotWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # Segmentation selector
    #
    self.segmentationSelector = slicer.qMRMLNodeComboBox()
    self.segmentationSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
    self.segmentationSelector.selectNodeUponCreation = True
    self.segmentationSelector.addEnabled = False
    self.segmentationSelector.removeEnabled = False
    self.segmentationSelector.noneEnabled = False
    self.segmentationSelector.showHidden = False
    self.segmentationSelector.showChildNodeTypes = False
    self.segmentationSelector.setMRMLScene( slicer.mrmlScene )
    self.segmentationSelector.setToolTip( "Pick the segmentation for the algorithm." )
    parametersFormLayout.addRow("Segmentation: ", self.segmentationSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.segmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    voxelArray = slicer.util.array(self.inputSelector.currentNode().GetID())
    self.numSlices = np.shape(voxelArray)[0]
    self.segmentationNode = self.segmentationSelector.currentNode()

  def onApplyButton(self):
    logic = SliceAreaPlotLogic()
    logic.run(self.numSlices, self.segmentationNode)

#
# SliceAreaPlotLogic
#

class SliceAreaPlotLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def run(self, numSlices, segmentationNode):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')

    # Get visible segment ID list.
    # Get segment ID list
    visibleSegmentIds = vtk.vtkStringArray()
    segmentationNode.GetDisplayNode().GetVisibleSegmentIDs(visibleSegmentIds)
    if visibleSegmentIds.GetNumberOfValues() == 0:
      logging.debug("computeStatistics will not return any results: there are no visible segments")

    tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Segment quantification")
    plotDataNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotDataNode")
    plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")

    for segmentIndex in range(visibleSegmentIds.GetNumberOfValues()):
      segmentID = visibleSegmentIds.GetValue(segmentIndex)
      vimage = segmentationNode.GetBinaryLabelmapRepresentation(segmentID)
      firstSlice = vimage.GetExtent()[4]
      lastSlice = vimage.GetExtent()[5]

      narray = vtk.util.numpy_support.vtk_to_numpy(vimage.GetPointData().GetScalars())
      vshape = vimage.GetDimensions()

      # Reshape the segment volume to have an array of slices
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

      slicer.util.updateTableFromArray(tableNode, areaBySliceInMm2)
      tableNode.GetTable().GetColumn(segmentIndex).SetName(segmentID)

      plotDataNode.SetAndObserveTableNodeID(tableNode.GetID())
      plotDataNode.SetXColumnName("Indexes")
      plotDataNode.SetYColumnName(tableNode.GetTable().GetColumn(segmentIndex).GetName())

      plotChartNode.AddAndObservePlotDataNodeID(plotDataNode.GetID())

    layoutManager = slicer.app.layoutManager()
    layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpPlotView)
    plotWidget = layoutManager.plotWidget(0)

    plotViewNode = plotWidget.mrmlPlotViewNode()
    plotViewNode.SetPlotChartNodeID(plotChartNode.GetID())

    logging.info('Processing completed')

    return True


class SliceAreaPlotTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SliceAreaPlot1()

  def test_SliceAreaPlot1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = SliceAreaPlotLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
