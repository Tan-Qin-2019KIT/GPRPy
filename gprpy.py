import os
import numpy as np
import matplotlib.pyplot as plt
import pickle
import toolbox.gprIO_DT1 as gprIO_DT1
import toolbox.gprIO_DZT as gprIO_DZT
import toolbox.gprpyTools as tools
import copy
import scipy.interpolate as interp
from pyevtk.hl import gridToVTK

class gprpy2d:
    def __init__(self,filename=None,desciption=None): #,profilerange=None):
        self.history = ["mygpr = gprpy.gprpy2d()"]

        # Initialize previous for undo
        self.previous = {}
        
        if filename is not None:
            self.importdata(filename)                 
        
    def importdata(self,filename):
        '''
        Loads .gpr (native GPRPy), .DT1 (Sensors and Software), or
        .DZT (GSSI) data files and populates all the gprpy2d fields.

        INPUT: 

        filename    name of the .gpr, DT1, or .DZT file you want to
                    import

        Last modified by plattner-at-alumni.ethz.ch, 5/22/2018
        '''
        
        file_name, file_ext = os.path.splitext(filename)
        
        if file_ext==".DT1":
            self.data=gprIO_DT1.readdt1(filename)
            self.info=gprIO_DT1.readdt1Header(file_name + ".HD")
            
            self.profilePos = np.linspace(self.info["Start_pos"],
                                          self.info["Final_pos"],
                                          self.info["N_traces"])

            self.twtt = np.linspace(self.info["TZ_at_pt"],
                                    self.info["Total_time_window"],
                                    self.info["N_pts_per_trace"])

            self.velocity = None
            self.depth = None
            self.maxTopo = None
            self.threeD = None
            # Initialize previous
            self.initPrevious()
            
            # Put what you did in history
            histstr = "mygpr.importdata('%s')" %(filename)
            self.history.append(histstr)                                
            
        elif file_ext==".DZT":

            self.data, self.info = gprIO_DZT.readdzt(filename)

            self.profilePos = self.info["startposition"]+np.linspace(0.0,
                                                                     self.data.shape[1]/self.info["scpmeter"],
                                                                     self.data.shape[1])
            
            self.twtt = np.linspace(0,self.info["nanosecptrace"],self.info["sptrace"])

            self.velocity = None
            self.depth = None
            self.maxTopo = None
            self.threeD = None
            # Initialize previous
            self.initPrevious()
            
            # Put what you did in history
            histstr = "mygpr.importdata('%s')" %(filename)
            self.history.append(histstr)
    
                      
        elif file_ext==".gpr":
            ## Getting back the objects:
            with open(filename, 'rb') as f:
                data, info, profilePos, twtt, history, velocity, depth, maxTopo, threeD = pickle.load(f)
            self.data = data
            self.info = info
            self.profilePos = profilePos
            self.twtt = twtt
            self.history = history
            self.velocity = velocity
            self.depth = depth
            self.maxTopo = maxTopo
            self.threeD = threeD
            
            # Initialize previous
            self.initPrevious()
            
        else:
            print("Can only read dt1 or dzt files")

    def showHistory(self):
        for i in range(0,len(self.history)):
            print(self.history[i])

    def writeHistory(self,outfilename="myhistory.py"):
        with open(outfilename,"w") as outfile:
            outfile.write("import gprpy\n")
            for i in range(0,len(self.history)):
                outfile.write(self.history[i] + "\n")
                
    def undo(self):
        self.data = self.previous["data"]
        self.twtt = self.previous["twtt"]
        self.info = self.previous["info"]
        self.profilePos = self.previous["profilePos"]
        self.velocity = self.previous["velocity"]
        self.depth = self.previous["depth"]
        self.maxTopo = self.previous["maxTopo"]
        self.threeD = self.previous["threeD"]
        # Make sure to not keep deleting history
        # when applying undo several times. 
        histsav = copy.copy(self.previous["history"])
        del histsav[-1]
        self.history = histsav
        print("undo")

        
    def initPrevious(self):
        self.previous["data"] = self.data
        self.previous["twtt"] = self.twtt 
        self.previous["info"] = self.info
        self.previous["profilePos"] = self.profilePos
        self.previous["velocity"] = self.velocity
        self.previous["depth"] = self.depth
        self.previous["maxTopo"] = self.maxTopo
        self.previous["threeD"] = self.threeD
        histsav = copy.copy(self.history)
        self.previous["history"] = histsav

        

    def save(self,filename):
        # Saving the objects:
        # Want to force the file name .gpr
        file_name, file_ext = os.path.splitext(filename)
        if not(file_ext=='.gpr'):
            filename = filename + '.gpr'
        with open(filename, 'wb') as f:  
            pickle.dump([self.data, self.info, self.profilePos, self.twtt, self.history,self.velocity,self.depth,self.maxTopo,self.threeD], f)
        print("Saved " + filename)
        # Add to history string
        histstr = "mygpr.save('%s')" %(filename)
        self.history.append(histstr)



    
    # This is a helper function
    def prepProfileFig(self, color="gray", contrast=1.0, yrng=None, xrng=None, asp=None):
        stdcont = np.nanmax(np.abs(self.data)[:])       
        
        if self.velocity is None:
            plt.imshow(self.data,cmap=color,extent=[min(self.profilePos),
                                                    max(self.profilePos),
                                                    max(self.twtt),
                                                    min(self.twtt)],
                       aspect="auto",vmin=-stdcont/contrast, vmax=stdcont/contrast)
            plt.gca().set_ylabel("two-way travel time [ns]")
            plt.gca().invert_yaxis()
            
        elif self.maxTopo is None:
             plt.imshow(self.data,cmap=color,extent=[min(self.profilePos),
                                                    max(self.profilePos),
                                                    max(self.depth),
                                                    min(self.depth)],
                    aspect="auto",vmin=-stdcont/contrast, vmax=stdcont/contrast)
             plt.gca().set_ylabel("depth [m]")
             plt.gca().invert_yaxis()
        else:
            plt.imshow(self.data,cmap=color,extent=[min(self.profilePos),
                                                    max(self.profilePos),
                                                    self.maxTopo-max(self.depth),
                                                    self.maxTopo-min(self.depth)],
                    aspect="auto",vmin=-stdcont/contrast, vmax=stdcont/contrast)            
            plt.gca().set_ylabel("elevation [m]")
            
            
        if yrng is not None:
            plt.ylim(yrng)
            
        if xrng is not None:
            plt.xlim(xrng)

        if asp is not None:
            plt.gca().set_aspect(asp)

        plt.gca().get_xaxis().set_visible(True)
        plt.gca().get_yaxis().set_visible(True)                
        plt.gca().set_xlabel("profile position")
        plt.gca().xaxis.tick_top()
        plt.gca().xaxis.set_label_position('top')
        
        return contrast, color, yrng, xrng, asp
       
    
    def showProfile(self, **kwargs):
        self.prepProfileFig(**kwargs)
        plt.show(block=False)


    def printProfile(self, figname, dpi=None, **kwargs):
        contrast, color, yrng, xrng, asp = self.prepProfileFig(**kwargs)
        plt.savefig(figname, format='pdf', dpi=dpi)
        plt.close('all')
        # Put what you did in history
        histstr = "mygpr.printProfile('%s', color='%s', contrast=%g, yrng=[%g,%g], xrng=[%g,%g], asp=%g, dpival=%d)" %(figname,color,contrast,yrng[0],yrng[1],xrng[0],xrng[1],asp,dpi)
        self.history.append(histstr)
        

    ####### Processing #######

    def setRange(self,minPos,maxPos):
        # Adjust the length of the profile, in case the trigger wheel is not
        # Calibrated
        # Store previous state for undo
        self.storePrevious()
        self.profilePos=np.linspace(minPos,maxPos,np.size(self.profilePos))
        histstr = "mygpr.setRange(%g,%g)" %(minPos,maxPos)
        self.history.append(histstr)
    

    def timeZeroAdjust(self):
        # Store previous state for undo
        self.storePrevious()        
        self.data = tools.timeZeroAdjust(self.data)      
        # Put what you did in history
        histstr = "mygpr.timeZeroAdjust()"
        self.history.append(histstr)


    def adjProfile(self,minPos,maxPos):
        # Store previous state for undo
        self.storePrevious()
        # set new profile positions
        self.profilePos = np.linspace(minPos,maxPos,len(self.profilePos))       
        # Put what you did in history
        histstr = "mygpr.adjProfile(%g,%g)" %(minPos,maxPos)
        self.history.append(histstr)   

        
    def setZeroTime(self,newZeroTime):
        # Store previous state for undo
        self.storePrevious()
        # Find index of value that is nearest to newZeroTime
        zeroind = np.abs(self.twtt - newZeroTime).argmin() 
        # Cut out everything before
        self.twtt = self.twtt[zeroind:] - newZeroTime
        self.data = self.data[zeroind:,:]
        # Put what you did in history
        histstr = "mygpr.setZeroTime(%g)" %(newZeroTime)
        self.history.append(histstr)  

        
    def dewow(self,window):
        # Store previous state for undo
        self.storePrevious()
        self.data = tools.dewow(self.data,window)
        # Put in history
        histstr = "mygpr.dewow(%d)" %(window)
        self.history.append(histstr)


    def remMeanTrace(self,ntraces):
        # Store previous state for undo
        self.storePrevious()
        # apply
        self.data = tools.remMeanTrace(self.data,ntraces)        
        # Put in history
        histstr = "mygpr.remMeanTrace(%d)" %(ntraces)
        self.history.append(histstr)


    def tpowGain(self,power=0.0):
        # Store previous state for undo
        self.storePrevious()
        # apply tpowGain
        self.data = tools.tpowGain(self.data,self.twtt,power)
        # Put in history
        histstr = "mygpr.tpowGain(%g)" %(power)
        self.history.append(histstr)

    def agcGain(self,window=10):
        # Store previous state for undo
        self.storePrevious()
        # apply agcGain
        self.data = tools.agcGain(self.data,window)
        # Put in history
        histstr = "mygpr.agcGain(%d)" %(float(window))
        self.history.append(histstr)
        

    def setVelocity(self,velocity):
        # Store previous state for undo
        self.storePrevious()

        self.velocity = velocity
        self.depth = self.twtt * velocity/2.0

        # Put in history
        histstr = "mygpr.setVelocity(%g)" %(velocity)
        self.history.append(histstr)


    def truncateY(self,maxY):
        # Store previous state for undo
        self.storePrevious()
        if self.velocity is None:
            maxtwtt = maxY
            maxind = np.argmin( np.abs(self.twtt-maxY) )
            self.twtt = self.twtt[0:maxind]
            self.data = self.data[0:maxind,:]
        else:
            maxtwtt = maxY*2.0/self.velocity
            maxind = np.argmin( np.abs(self.twtt-maxtwtt) )
            self.twtt = self.twtt[0:maxind]
            self.data = self.data[0:maxind,:]
            self.depth = self.depth[0:maxind]
        # Put in history
        histstr = "mygpr.truncateY(%g)" %(maxY)
        self.history.append(histstr)


        
    def topoCorrect(self,topofile,delimiter=','):
        if self.velocity is None:
            print("First need to set velocity!")
            return
        # Store previous state for undo
        self.storePrevious()
        self.data_pretopo = self.data
        topoPos, topoVal, self.threeD = tools.prepTopo(topofile,delimiter)
        self.data, self.twtt, self.maxTopo = tools.correctTopo(self.data, velocity=self.velocity,
                                                              profilePos=self.profilePos, topoPos=topoPos,
                                                              topoVal=topoVal, twtt=self.twtt)
        # Put in history
        if delimiter is ',':
            histstr = "mygpr.topoCorrect('%s')" %(topofile)
        else:
            histstr = "mygpr.topoCorrect('%s',delimiter='\\t')" %(topofile)
        self.history.append(histstr)
        


    def exportVTK(self,outfile,gpsfile=None,thickness=0.1,delimiter=',',aspect=1.0,smooth=True, win_length=51, porder=3):
        # First get the x,y,z positions of our data points
        x,y,z = tools.prepVTK(self.profilePos,gpsfile,delimiter,smooth,win_length,porder)        
        z = z*aspect     
        if self.velocity is None:
            downward = self.twtt*aspect
        else:
            downward = self.depth*aspect                        
        if self.maxTopo is None:
            topY = 0
        else:
            topY=self.maxTopo
            
        Z = topY - np.reshape(downward,(1,len(downward))) + np.reshape(z,(len(z),1))
        ZZ = np.tile(np.reshape(Z, (1,Z.shape[0],Z.shape[1])), (3,1,1))
        
        # This is if we want everything on the x axis.
        #X = np.tile(np.reshape(self.profilePos,(len(self.profilePos),1)),(1,len(downward)))
        #XX = np.tile(np.reshape(X, (X.shape[0],1,X.shape[1])), (1,2,1))
        #YY = np.tile(np.reshape([-thickness/2,thickness/2],(1,2,1)), (len(x),1,len(downward)))

        # To create a 3D grid with a width, calculate the perpendicular direction,
        # normalize it, and add it to xvals and yvals as below.
        # To figure this out, just drar the profile point-by-point, and at each point,
        # draw the perpendicular to the segment and place a grid point in each perpendicular
        # direction
        #
        #          x[0]-px[0], x[1]-px[1], x[2]-px[2], ..... 
        # xvals =     x[0]   ,    x[1]   ,     x[2]  , .....   
        #          x[0]+px[0], x[1]+px[1], x[2]+px[2], .....
        #  
        #          y[0]+py[0], y[1]+py[1], y[2]+py[2], .....
        # yvals =     y[0]   ,    y[1]   ,    y[2]   , .....
        #          y[0]-py[0], y[1]-py[1], y[2]-py[2], .....
        #
        # Here, the [px[i],py[i]] vector needs to be normalized by the thickness 
        pvec = np.asarray([(y[0:-1]-y[1:]).squeeze(), (x[1:]-x[0:-1]).squeeze()])
        pvec = np.divide(pvec, np.linalg.norm(pvec,axis=0)) * thickness/2.0
        # We can't calculate the perpendicular direction at the last point
        # let's just set it to the same as for the second-to-last point
        pvec = np.append(pvec, np.expand_dims(pvec[:,-1],axis=1) ,axis=1)
        
        X = np.asarray([(x.squeeze()-pvec[0,:]).squeeze(), x.squeeze(), (x.squeeze()+pvec[0,:]).squeeze()])
        Y = np.asarray([(y.squeeze()+pvec[1,:]).squeeze(), y.squeeze(), (y.squeeze()-pvec[1,:]).squeeze()])
        # Copy-paste the same X and Y positions for each depth
        XX = np.tile(np.reshape(X, (X.shape[0],X.shape[1],1)), (1,1,ZZ.shape[2]))
        YY = np.tile(np.reshape(Y, (Y.shape[0],Y.shape[1],1)), (1,1,ZZ.shape[2]))
        
        if self.maxTopo is None:
            data=self.data.transpose()
        else:
            data=self.data_pretopo.transpose()       

        data = np.asarray(data)
        data = np.reshape(data,(1,data.shape[0],data.shape[1]))        
        data = np.tile(data, (3,1,1))
        
        # Remove the last row and column to turn it into a cell
        # instead of point values 
        data = data[0:-1,0:-1,0:-1]

        nx=3-1
        ny=len(x)-1
        nz=len(downward)-1
        datarray = np.zeros(nx*ny*nz).reshape(nx,ny,nz)
        datarray[:,:,:] = data
        
        gridToVTK(outfile,XX,YY,ZZ, cellData ={'gpr': datarray})
 
        # Put in history
        if gpsfile is None:
            histstr = "mygpr.exportVTK('%s',aspect=%g)" %(outfile,aspect)
        else:
            if delimiter is ',':
                histstr = "mygpr.exportVTK('%s',gpsfile='%s',thickness=%g,delimiter=',',aspect=%g,smooth=%r, win_length=%d, porder=%d)" %(outfile,gpsfile,thickness,aspect,smooth,win_length,porder)
            else:
                 histstr = "mygpr.exportVTK('%s',gpsfile='%s',thickness=%g,delimiter='\\t',aspect=%g,smooth=%r, win_length=%d, porder=%d)" %(outfile,gpsfile,thickness,aspect,smooth,win_length,porder)
        self.history.append(histstr)

        

        
    def storePrevious(self):        
        self.previous["data"] = self.data
        self.previous["twtt"] = self.twtt
        self.previous["info"] = self.info
        self.previous["profilePos"] = self.profilePos
        self.previous["history"] = self.history
        self.previous["velocity"] = self.velocity
        self.previous["depth"] = self.depth
        self.previous["maxTopo"] = self.maxTopo
        self.previous["threeD"] = self.threeD
