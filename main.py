from __future__ import division
from tkinter import *

# import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=YES)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = ''
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        
        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.dirPanel = Frame(self.frame)
        self.dirPanel.grid(row = 0, column = 0, columnspan = 3, sticky = W)
        self.lb1 = Label(self.dirPanel, text = "Image Dir:")
        self.lb1.grid(row = 0, column = 0, sticky = W)
        self.entry = Entry(self.dirPanel)
        self.entry.grid(row = 0, column = 1, sticky = W)
        self.ldBtn = Button(self.dirPanel, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W)        
        
        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 0, column = 3, columnspan = 2, sticky = W)
        self.lb3 = Label(self.ctrPanel, text = 'Navigate:')
        self.lb3.pack(side = LEFT, padx = 1, pady = 1)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 5, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 1, pady = 1)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 5, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 1, pady = 1)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 1)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 1)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # showing bbox info & delete bbox
        self.bboxPanel = Frame(self.frame)
        self.bboxPanel.grid(row = 1, column = 3, columnspan = 3, sticky = W+E)
        self.lb2 = Label(self.bboxPanel, text = 'Bounding boxes:')
        self.lb2.grid(row = 1, column = 0,  sticky = W)
        self.listbox = Listbox(self.bboxPanel, height = 5, width = 33)
        self.listbox.grid(row = 1, column = 1, rowspan = 3, sticky = W+E)
        self.btnDel = Button(self.bboxPanel, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 1, column = 2, sticky = W+N)
        self.btnClear = Button(self.bboxPanel, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 2, column = 2, sticky = W+N)
        self.btnStore = Button(self.bboxPanel, text = 'StoreAll', command = self.saveImage)
        self.btnStore.grid(row = 3, column = 2, sticky = W+N)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.grid(row = 3, column = 0, rowspan = 2, columnspan=6, sticky = W+N+E+S)
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        scrollbar1 = Scrollbar(self.mainPanel, orient=VERTICAL)
        scrollbar1.pack(side=RIGHT, fill=Y)
        scrollbar1.config(command=self.mainPanel.yview)
        scrollbar2 = Scrollbar(self.mainPanel, orient=HORIZONTAL)
        scrollbar2.pack(side=BOTTOM, fill=X)
        scrollbar2.config(command=self.mainPanel.xview)
        self.mainPanel.config(xscrollcommand=scrollbar2.set, yscrollcommand=scrollbar1.set)
        
        

        # for debugging
#        self.setImage()
#        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = s
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
        # get image list
        self.imageDir = os.path.join(r'./Images', '%s' %(self.category))
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            print ('No .jpg images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '%s' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)


        self.loadImage()
        print ('%d images loaded from %s' %(self.total, s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = self.tkimg.width(), height = self.tkimg.height())
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))
        self.mainPanel.config(scrollregion=(0, 0, self.tkimg.width(), self.tkimg.height()))
        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    tmp = [int(t.strip()) for t in line.split()]
##                    print tmp
                    self.bboxList.append(tuple(tmp))
                    tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1], \
                                                            tmp[2], tmp[3], \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(tmp[0], tmp[1], tmp[2], tmp[3]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print ('Image No. %d saved' %(self.cur))


    def mouseClick(self, event):
        canvas = event.widget
        canvasx = canvas.canvasx(event.x)
        canvasy = canvas.canvasy(event.y)
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = canvasx, canvasy
        else:
            x1, x2 = min(self.STATE['x'], canvasx), max(self.STATE['x'], canvasx)
            y1, y2 = min(self.STATE['y'], canvasy), max(self.STATE['y'], canvasy)
            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        canvas = event.widget
        canvasx = canvas.canvasx(event.x)
        canvasy = canvas.canvasy(event.y)
        self.disp.config(text = 'x: %d, y: %d' %(canvasx, canvasy))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, canvasy, self.tkimg.width(), canvasy, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(canvasx, 0, canvasx, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            canvasx, canvasy, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
