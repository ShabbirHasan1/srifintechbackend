from pychartjs import BaseChart, ChartType, Color, Options

import json
from random import randint


def oichange_newbardata(data,fill,borderWidth=None,backgroundColor=None, borderColor=None):
    class NewBarData: 
        def __init__(self, data, fill, borderWidth=None,backgroundColor=None, borderColor=None): 
            self.data            = data
            #Border properties
            self.borderColor     = borderColor
            self.borderWidth     = borderWidth
            self.backgroundColor = backgroundColor
            self.fill            = fill

def oichange_bargraph(closest_strike,annotation_label):
    class BarGraph(BaseChart):

        type = ChartType.Bar
        
        class labels:
            xaxis_labels = list()

        class data:
            class bardata1:     #This is for Plotting PUTOI
                    label           = "Call OI"
                    data            = []
                    #Border properties
                    borderColor     = Color.Black
                    borderWidth     = 1
                    backgroundColor = Color.Red
                    fill            = True

            class bardata2:     #This is for Plotting PUTOI
                    label           = "Put OI"
                    data            = []
                    #Border properties
                    borderColor     = Color.Black
                    borderWidth     = 1
                    backgroundColor = Color.Green
                    fill            = True

        class options:
            responsive = True
            tooltips = {
                            "intersect"         : False,
                            # "mode"              : "nearest",
                            "mode"              : "index",
                            "axis"              : "x",
                            "position"          : "nearest",
                            "displayColors"     : True
                            # "cornerRadius"      : 3
            }
            
    #         # title = Options.Title(text="MULTI STRIKE OI CHART", fontsize=18)
    #         # showLines = False # This will not draw lines between points
    #         # title = {   
    #         #             "display"           : True,
    #         #             "text"              : "sample title",
    #         #             "fontSize"          : 20,
    #         #             "fontColor"         : Color.Green
    #         # }

    #         # legend = Options.Legend(position="bottom")
            legend = {
                            'position'      : 'top', 
                            'labels'        : {
                            'fontColor'     : Color.Black, 
                            "boxWidth"      : 35,
                            # 'fullWidth'   : True,
                            "fontSize"      : 16,
                            "fontStyle"     : "bold"
                            # "padding"     : 50,
                            # "usePointStyle" : True
                        }
            }
            
    #         layout = {
    #                     "padding"   :  {
    #                                     "left"    : 0,
    #                                     "right"   : 0,
    #                                     "top"     : 0,
    #                                     "bottom"  : 20
    #                 }
    #         }
            # scales = {
            #             "xAxes": [{
            #                     "display"   : True,
            #                     "labelString" : "HELLOO",
            #                     "gridLines": {
            #                         "offsetGridLines": False
            #                     }
            #             }],
            #             "yAxes": [{
            #                     "gridLines": {
            #                         "offsetGridLines": False
            #                     }
            #             }]
            # }

            scales = {

                "xAxes": [
                        {   
                           
                           "display"        : True,
                           "labelString"    : "Strike Prices" ,
                            "gridLines"     : {
                                "display"      : True,
                                "drawBorder"   : True
                            }, 
                    }
                ],
                "yAxes": [
                        {
                            "scaleLabel": {
                                            "display"       : True,
                                            "labelString"   : "Open Interest",
                                            "fontColor"     : Color.Black,
                                            "fontSize"      : 16
                                }, 
                            "id"            : "y1",
                            "position"      : "left",
                            "display"       : True,
                            "gridLines"     : {
                                                "display"     : True
                                            # "drawBorder"    : True
                        }
                    }
                   
                ]
            }
        # class pluginOptions:
        #     zoom = {
        #         "pan": {
        #                       "enabled": True,
        #                       "mode": "x",
        #                       "speed": 10,
        #                       "threshold": 10
        #         },
        #         "zoom" : {
        #             "enabled" : True,
        #             "mode": "y"
        #         }
        #     } 

    BarGraph.options.annotation = {
                    "annotations": [
                    {
                        "drawTime": "beforeDatasetsDraw",
                        "id": "vline",
                        "type": "line",
                        "mode": "vertical",
                        "scaleID": "x-axis-0",  
                        "value": closest_strike,
                        "borderColor": Color.Black,
                        "borderWidth": 5,
                        "label": {
                            "backgroundColor": Color.Hex("#7A9B0E"),
                            "content": annotation_label,
                            "enabled": True,
                            "position" : "top"
                        }
                    },          
                    ]
            }

    return BarGraph


def strangle_newline(data, fill, label, yAxisID,borderColor=None):
	color_palette = [
					Color.Red,
					Color.Blue,
					Color.Purple,
					Color.Maroon,
					Color.Magenta,
					Color.Teal,
					Color.Navy,
					Color.Orange,
					Color.Cyan,
					Color.Lime,
					Color.Olive,
					Color.Brown, 
					Color.Pink,
					Color.Lavender,
					Color.Mint,
					Color.Apricot,
					Color.Beige,
					Color.Yellow,
					Color.White
	]
	# color_count = len(strangle_strike_list) # Changing
	# color_count = len(color_count_list)
	def get_random_hexcolor():
		return '#{:06x}'.format(randint(0, 256**3))

	borderColor = color_palette[borderColor]
	# LineData  
	class NewLineData: 
		def __init__(self,): 
			self.data		   = data
			self.fill		   = fill
			self.label		  = label
			self.yAxisID		= yAxisID
			#Border properties
			self.borderColor	= borderColor
			self.borderWidth	= 2
			self.lineTension	= 0
			#Point Properties
			self.pointRadius	= 1
	return NewLineData

def strangle_linegraph(label_ticker,scale_label_str):
	class LineGraph(BaseChart):

		type = ChartType.Line
		class labels:
			xaxis_labels = list()

		class data:
			class linedata:
				# label		   = ticker # Changing
				label = ""
				data			= []
				#Border properties
				borderColor	 = Color.Black
				borderColor	 = Color.Hex("#7A9B0E")
				borderWidth	 = 3
				fill			= False
				yAxisID		 = 'y1'
				lineTension	 = 0
				pointStyle = 'triangle'
				borderDash	  = [3, 1] 
				#Point Properties
				pointRadius	 = 1

		class options:
			responsive = True
			tooltips = {
							"intersect"		 : False,
			}
			legend = {
							'position'	  : 'top', 
							'labels'		: {
							'fontColor'	 : Color.Black, 
							"boxWidth"	  : 35,
							"fontSize"	  : 10,
							"fontStyle"	 : "bold"
						}
			}
			layout = {
						"padding"   :  {
										"left"	: 0,
										"right"   : 0,
										"top"	 : 0,
										"bottom"  : 20
					}
			}
			scales = {} # Changing
	LineGraph.data.linedata.label = label_ticker
	LineGraph.options.scales = {
				"xAxes": [
						{   
							"display"		: True,
							"gridLines"	 : {
								"display"	  : False,
								"drawBorder"   : True
							}, 
					}
				],

				"yAxes": [
						{
							"scaleLabel": {
											"display"	   : True,
											"labelString"   : label_ticker,
											"fontColor"	 : Color.Black
							}, 
							"id"			: "y1",
							"position"	  : "right",
							"display"	   : True,
							"gridLines"	 : {
												"display"	 : False
						}
					},
					{
						"scaleLabel": {
											"display"	   : True,
											"labelString"   : scale_label_str,
											"fontColor"	 : Color.Black
						}, 
						"id"			: "y2",
						"position"	  : "left",
						"gridLines"	 : {
										"display"	   : True
						}
					}
				]
			}
	return LineGraph

def maxpain_newline(data, fill, label, yAxisID,borderColor=None):
	color_palette = [
					Color.Red,
					Color.Blue,
					Color.Purple,
					Color.Maroon,
					Color.Magenta,
					Color.Teal,
					Color.Navy,
					Color.Orange,
					Color.Cyan,
					Color.Lime,
					Color.Olive,
					Color.Brown, 
					Color.Pink,
					Color.Lavender,
					Color.Mint,
					Color.Apricot,
					Color.Beige,
					Color.Yellow,
					Color.White
	]
	# color_count = len(strangle_strike_list) # Changing
	# color_count = len(color_count_list)
	def get_random_hexcolor():
		return '#{:06x}'.format(randint(0, 256**3))

	borderColor = color_palette[borderColor]
	# LineData  
	class NewLineData: 
		def __init__(self,): 
			self.data		   = data
			self.fill		   = fill
			self.label		  = label
			self.yAxisID		= yAxisID
			#Border properties
			self.borderColor	= borderColor
			self.borderWidth	= 2
			self.lineTension	= 0
			#Point Properties
			self.pointRadius	= 1
	return NewLineData

def maxpain_linegraph(label_ticker,scale_label_str):
	class LineGraph(BaseChart):
		type = ChartType.Line
		class labels:
			xaxis_labels = list()

		class data:
			class linedata1:
				# label		   = ticker # Changing
				label = ""
				data			= []
				#Border properties
				# borderColor	 = Color.Black
				borderColor	 = Color.Hex("#DC143C")
				borderWidth	 = 3
				fill			= False
				yAxisID		 = 'y1'
				lineTension	 = 0
				pointStyle = 'triangle'
				borderDash	  = [3, 1] 
				#Point Properties
				pointRadius	 = 1

			class linedata2:
				# label		   = ticker # Changing
				label = ""
				data			= []
				#Border properties
				borderColor	 = Color.Hex("#7A9B0E")	
				# borderColor	 = Color.Green
				borderWidth	 = 3
				fill			= False
				yAxisID		 = 'y1'
				lineTension	 = 0
				pointStyle = 'triangle'
				borderDash	  = [3, 1] 
				#Point Properties
				pointRadius	 = 1

		class options:
			responsive = True
			tooltips = {
							"intersect"		 : False,
			}
			legend = {
							'position'	  : 'top', 
							'labels'		: {
							'fontColor'	 : Color.Black, 
							"boxWidth"	  : 35,
							"fontSize"	  : 10,
							"fontStyle"	 : "bold"
						}
			}
			layout = {
						"padding"   :  {
										"left"	: 0,
										"right"   : 0,
										"top"	 : 0,
										"bottom"  : 20
					}
			}
			scales = {} # Changing
	LineGraph.data.linedata1.label = scale_label_str
	LineGraph.data.linedata2.label = label_ticker
	LineGraph.options.scales = {
				"xAxes": [
						{   
							"display"		: True,
							"gridLines"	 : {
								"display"	  : False,
								"drawBorder"   : True
							}, 
					}
				],

				"yAxes": [
					{
						"scaleLabel": {
											"display"	   : True,
											"labelString"   : scale_label_str,
											"fontColor"	 : Color.Black
						}, 
						"id"			: "y1",
						"position"	  : "left",
						"gridLines"	 : {
										"display"	   : True
						}
					}
				]
			}
	return LineGraph

def pcr_newline(data, fill, label, yAxisID,borderColor=None):
	color_palette = [
					Color.Red,
					Color.Blue,
					Color.Purple,
					Color.Maroon,
					Color.Magenta,
					Color.Teal,
					Color.Navy,
					Color.Orange,
					Color.Cyan,
					Color.Lime,
					Color.Olive,
					Color.Brown, 
					Color.Pink,
					Color.Lavender,
					Color.Mint,
					Color.Apricot,
					Color.Beige,
					Color.Yellow,
					Color.White
	]
	# color_count = len(strangle_strike_list) # Changing
	# color_count = len(color_count_list)
	def get_random_hexcolor():
		return '#{:06x}'.format(randint(0, 256**3))

	borderColor = color_palette[borderColor]
	# LineData  
	class NewLineData: 
		def __init__(self,): 
			self.data		   = data
			self.fill		   = fill
			self.label		  = label
			self.yAxisID		= yAxisID
			#Border properties
			self.borderColor	= borderColor
			self.borderWidth	= 2
			self.lineTension	= 0
			#Point Properties
			self.pointRadius	= 1
	return NewLineData

def pcr_linegraph(label_ticker,scale_label_str):
	class LineGraph(BaseChart):
		type = ChartType.Line
		class labels:
			xaxis_labels = list()

		class data:
			class linedata1:
				# label		   = ticker # Changing
				label = ""
				data			= []
				#Border properties
				# borderColor	 = Color.Black
				borderColor	 = Color.Hex("#DC143C")
				borderWidth	 = 3
				fill			= False
				yAxisID		 = 'y1'
				lineTension	 = 0
				pointStyle = 'triangle'
				borderDash	  = [3, 1] 
				#Point Properties
				pointRadius	 = 1

			class linedata2:
				# label		   = ticker # Changing
				label = ""
				data			= []
				#Border properties
				borderColor	 = Color.Hex("#7A9B0E")	
				# borderColor	 = Color.Green
				borderWidth	 = 3
				fill			= False
				yAxisID		 = 'y2'
				lineTension	 = 0
				pointStyle = 'triangle'
				borderDash	  = [3, 1] 
				#Point Properties
				pointRadius	 = 1

		class options:
			responsive = True
			tooltips = {
							"intersect"		 : False,
			}
			legend = {
							'position'	  : 'top', 
							'labels'		: {
							'fontColor'	 : Color.Black, 
							"boxWidth"	  : 35,
							"fontSize"	  : 10,
							"fontStyle"	 : "bold"
						}
			}
			layout = {
						"padding"   :  {
										"left"	: 0,
										"right"   : 0,
										"top"	 : 0,
										"bottom"  : 20
					}
			}
			scales = {} # Changing
	LineGraph.data.linedata1.label = scale_label_str
	LineGraph.data.linedata2.label = label_ticker
	LineGraph.options.scales = {
				"xAxes": [
						{   
							"display"		: True,
							"gridLines"	 : {
								"display"	  : False,
								"drawBorder"   : True
						}, 
					}
				],

				"yAxes": [
					{
						
						"scaleLabel": {
										"display"	   : True,
										"labelString"   : scale_label_str,
										"fontColor"	 : Color.Black
						}, 
						"id"			: "y1",
							"position"	  : "left",
							"display"	   : True,
							"gridLines"	 : {
												"display"	 : False
						}

					},
					{
						"scaleLabel": {
											"display"	   : True,
											"labelString"   : label_ticker,
											"fontColor"	 : Color.Black
						}, 
						"id"			: "y2",
						"position"	  : "right",
						"gridLines"	 : {
										"display"	   : True
						}
					}
				]
			}
	return LineGraph

def gl_bargraph(data1,yaxis_labels,y_label,top_label,barcolor="GREEN",position='left',len1=None,len2=None):
    class BarGraph(BaseChart):

        type = ChartType.HorizontalBar
        
        class labels:
            yaxis_labels = list()

        class data:
            pass

        class options:
            indexAxis = 'y'
            responsive = True
            tooltips = {
                            "intersect"         : False,
                            # "mode"              : "nearest",
                            "mode"              : "index",
                            "axis"              : "y",
                            "position"          : "nearest",
                            "displayColors"     : True
                            # "cornerRadius"      : 3
            }

            legend = {
                            'position'      : 'top', 
                            'labels'        : {
                            'fontColor'     : Color.Black, 
                            "boxWidth"      : 35,
                            # 'fullWidth'   : True,
                            "fontSize"      : 16,
                            "fontStyle"     : "bold"
                            # "padding"     : 50,
                            # "usePointStyle" : True
                        }
            }
            

            scales = None

    class bardata1:
        label           = "Gainers Losers"
        data            = []
        axis            = 'y'
        #Border properties
        borderColor     = Color.Black
        borderWidth     = 1
        backgroundColor = None
        fill            = True

    class bardata2:
        label           = "Gainers Losers"
        data            = []
        axis            = 'y'
        #Border properties
        borderColor     = Color.Black
        borderWidth     = 1
        backgroundColor = None
        fill            = True



    BarGraph.data.bardata1 = bardata1
    BarGraph.data.bardata1.data = data1
    BarGraph.labels.yaxis_labels = yaxis_labels
    BarGraph.data.bardata1.backgroundColor = Color.Green if barcolor == "GREEN" \
                                            else Color.Red if  barcolor == "RED" \
                                            else ([Color.Green]*len1)+([Color.Red]*len2)
    BarGraph.data.bardata1.label = top_label

    # if data2 is not None: 
    #     BarGraph.data.bardata2 = bardata2
    #     BarGraph.data.bardata2.data = data2
    #     BarGraph.data.bardata2.backgroundColor = Color.Red
    #     BarGraph.data.bardata2.label = "LOOSERS"

    BarGraph.options.scales = {

                "xAxes": [
                        {   
                           
                           "display"        : True,
                           "labelString"    : "Percent Gain" ,
                            "gridLines"     : {
                                "display"      : True,
                                "drawBorder"   : True
                            }, 
                    }
                ],
                "yAxes": [
                        {
                            "scaleLabel": {
                                            "display"       : True,
                                            "labelString"   : "NSE "+y_label,
                                            "fontColor"     : Color.Black,
                                            "fontSize"      : 16
                                }, 
                            "id"            : "y1",
                            "position"      : position,
                            "display"       : True,
                            "gridLines"     : {
                                                "display"     : True
                                            # "drawBorder"    : True
                        }
                    }
                   
                ]
            }

    return BarGraph