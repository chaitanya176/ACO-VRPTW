from scipy.spatial import distance
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sqlite3

sys.path.insert(0, 'C:/Users/Lada/Documents/ACO/ACO-VRPTW')
from aco_funs import *
from aco_vrptw import *


dtb='data_files/medSched.sqlite'
newMbr={}
newMbr['service_time']=3

class newAppt(QWidget):
    def __init__(self,parent=None):
        QWidget.__init__(self, parent)
        layout = QGridLayout()
        
        lbFont=QFont()
        lbFont.setPointSize(10)
        lbFont.setBold(True)
        
        self.cmAvl=False
        self.FirstAppt=False
        self.resDataM=[]
        self.resSolution={}

        self.lbTitle=QLabel('                           Create New Appointment                          ')
        self.lbTitle.setFont(lbFont)
        
        self.mbr1=mbrSelection()
        self.slds=sliders()
        self.checkAveB=QPushButton('Check Availability')
        self.checkAveB.clicked.connect(self.checkAvb)
        
        self.appStatL=QLabel('')
        
        self.confB=QPushButton('Confirm')
        self.confB.clicked.connect(self.confirmAvb)
        
        layout.addWidget(self.lbTitle,1,1,1,2)
        layout.addWidget(self.mbr1,2,1,1,2)
        layout.addWidget(self.slds,3,1,1,2)
        layout.addWidget(self.checkAveB,4,1,1,2)
        layout.addWidget(self.appStatL,5,1,1,1)
        layout.addWidget(self.confB,5,2,1,1)

        self.setLayout(layout)
        
    #Checking Availability 
    #ACO VRPTW Implementation
    def checkAvb(self):
        print('checking availability')
        #create DataM
        conn=sqlite3.connect(dtb)
        c=conn.cursor()
        svc_dt=cal1.selectedDate().toPyDate()
        c.execute('''select mbr_id, 
                            svc_tm_from,
                            svc_tm_to,
                            svc_len
                    from    schedule
                    where   svc_dt =?''',(svc_dt,))
        
        recs=c.fetchall()
        
        if len(recs)==0:
            #first appointment
            print('first appointment')
            self.cmAvl=True
            self.FirstAppt=True
            self.appStatL.setText('AVAILABLE')
        else:
            self.FirstAppt=False
            dataM=[]
            custList=[0]
            rec0={}
            
            #depo data
            rec0['cust_no']=0
            rec0['ready_time']=0
            rec0['due_time']=1500
            rec0['service_time']=0
            dataM.append(rec0)

            #create dataM records for already created appointments
            for rec in recs:
                rec0={}
                print('printing rec',rec)
                rec0['cust_no']=rec[0]
                rec0['ready_time']=rec[1]
                rec0['due_time']=rec[2]
                rec0['service_time']=rec[3]
                dataM.append(rec0)
                custList.append(rec[0])


            try:
                #dataM record for the new appointment
                rec0={}
                rec0['cust_no']=newMbr['cust_no']
                rec0['ready_time']=newMbr['ready_time']
                rec0['due_time']=newMbr['due_time']
                rec0['service_time']=newMbr['service_time']
                dataM.append(rec0)
                custList.append(newMbr['cust_no'])

                print('cust_no',newMbr['cust_no']) 
                print('ready_time',newMbr['ready_time']) 
                print('due_time',newMbr['due_time']) 
                print('service_time',newMbr['service_time']) 
            except:
                print('SELECTION INCOMPLETE')
            

            #create distM
            distM=[]
            for cust1 in custList:
                d0M=[]
                for cust2 in custList:
                    c.execute(  '''
                        select  distinct    a.lat,
                                            a.lon,
                                            b.lat,
                                            b.lon,
                                            c.tme,
                                            c.crow_dist
                        from    mbrs a,
                                mbrs b,
                                distTme c
                        where   a.mbr_id = ? and
                                b.mbr_id = ? and
                                a.zip_cd = c.zip_cd1 and
                                b.zip_cd = c.zip_cd2

                                ''',(cust1,cust2,))
                    
                    recs=c.fetchall()
                    
                    coord_from=(recs[0][0],recs[0][1])
                    coord_to=(recs[0][2],recs[0][3])
                    tme0=recs[0][4]
                    crow0=recs[0][4]
                    crow1=round(distance.euclidean(coord_from,coord_to),5)
                    tme1=float(crow1*tme0/tme0)
                    d0M.append(round(tme1/5,2))
                distM.append(d0M)
                
            #Solution
            initSol=initSolution(0,dataM,distM)
            depo=0
            locCount=len(dataM)
            alpha=0.2
            BRCP=0.7
            iterCount=30
            colSize=20
                    
            solution=aco_run(dataM,distM,depo,locCount,initSol,alpha,BRCP,iterCount,colSize)
            print('aco sol vehcount',solution['vehicleCount'])
                    
            
            
            #getting cm availability
            c.execute('''   select cm_ct 
                            from cmAvlblt
                            where   svc_dt =?''',(svc_dt,))
            
            cm_ct=c.fetchall()[0][0]
            print('cm avail',cm_ct)
            
            if solution['vehicleCount'] <= cm_ct:
                print('We have enough CMs')
                self.cmAvl=True
                self.appStatL.setText('AVAILABLE')
            else:
                self.appStatL.setText('NOT AVAILABLE')
                self.cmAvl=False

            for veh in solution['vehicles']:
                print(veh['vehNum'],veh['tour'])
            

            self.resDataM=dataM
            self.resSolution=solution

        conn.close()

    def confirmAvb(self):
        print('confirming availability')
        svc_dt=cal1.selectedDate().toPyDate()
        
        conn=sqlite3.connect(dtb)
        c=conn.cursor()

        c.execute('''   Delete from schedule
                        where   svc_dt =?''',(svc_dt,))
        
        
        if self.cmAvl==True:
            if self.FirstAppt==True:
                mbr_id0=newMbr['cust_no']
                svc_from0=newMbr['ready_time']
                svc_to0=newMbr['due_time']
                svc_len0=newMbr['service_time']
                c.execute('''INSERT INTO schedule(cm_id,order_id,mbr_id,svc_dt,svc_tm_from,svc_tm_to,svc_len)
                             VALUES(?,?,?,?,?,?,?)''',(1,1,mbr_id0,svc_dt,svc_from0,svc_to0,svc_len0)) 
            else:
                for veh in self.resSolution['vehicles']:
                    order_id=1
                    for mbr in veh['tour']:
                        if mbr != 0:
                            cm_id0=veh['vehNum']
                            mbr_id0=self.resDataM[mbr]['cust_no']
                            svc_from0=self.resDataM[mbr]['ready_time']
                            svc_to0=self.resDataM[mbr]['due_time']
                            svc_len0=self.resDataM[mbr]['service_time']
                            c.execute('''INSERT INTO schedule(cm_id,order_id,mbr_id,svc_dt,svc_tm_from,svc_tm_to,svc_len)
                                         VALUES(?,?,?,?,?,?,?)''',(cm_id0,order_id,mbr_id0,svc_dt,svc_from0,svc_to0,svc_len0)) 
                            order_id+=1

        conn.commit() 
        conn.close() 
        self.appStatL.setText('CONFIRMED')
class mbrSelection(QWidget):
    def __init__(self,parent = None):
        QWidget.__init__(self, parent)
    
        layout = QGridLayout()
        
        tFont=QFont()
        tFont.setBold(True)

        self.lb1=QLabel('Member')
        self.lb1.setFont(tFont)
        
        self.tb1=QLineEdit()

        layout.addWidget(self.lb1,1,1)
        layout.addWidget(self.tb1,1,2)

        self.setLayout(layout)
        
        self.tb1.textChanged.connect(self.mbrChange) 
    
    def mbrChange(self,value):
        newMbr['cust_no']=value
        
class sliders(QWidget):

    clicked = pyqtSignal()

    def __init__(self,parent = None):
    
        QWidget.__init__(self, parent)
      


        tFont=QFont()
        tFont.setBold(True)
        
        self.resize(350,200)
        self.setFixedSize(350,200)


        #Slide 1
        self.lbNme1=QLabel('Service Window From:',self)
        self.lbVal1=QLabel('',self)

        self.lbNme1.setFont(tFont)
        self.lbVal1.setFont(tFont)

        self.lbNme1.move(10,10)
        self.lbVal1.move(250,10)

        self.slide1=QSlider(Qt.Horizontal,self)
        self.slide1.move(150,10)

        self.slide1.setRange(84,228)
        self.slide1.valueChanged[int].connect(self.slideChangeValue1)
    
        #Slide 2
        self.lbNme2=QLabel('Service Window To:',self)
        self.lbVal2=QLabel('',self)

        self.lbNme2.setFont(tFont)
        self.lbVal2.setFont(tFont)

        self.lbNme2.move(10,60)
        self.lbVal2.move(250,60)

        self.slide2=QSlider(Qt.Horizontal,self)
        self.slide2.move(150,60)
       
        self.slide2.setRange(84,228)
        self.slide2.valueChanged[int].connect(self.slideChangeValue2)
        
        #Slide 3
        self.lbNme3=QLabel('Appointment Length:',self)
        self.lbVal3=QLabel('',self)

        self.lbNme3.setFont(tFont)
        self.lbVal3.setFont(tFont)

        self.lbNme3.move(10,110)
        self.lbVal3.move(250,110)

        self.slide3=QSlider(Qt.Horizontal,self)
        self.slide3.move(150,110)
       
        self.slide3.setRange(3,24)
        self.slide3.valueChanged[int].connect(self.slideChangeValue3)
        
        self.lbVal3.setText(str(dispDuration(3)))
        self.lbVal3.adjustSize()
        

    def slideChangeValue1(self,value):
        self.lbVal1.setText(str(dispTime(value)))
        self.lbVal1.adjustSize()
        self.slide2.setRange(value+6,228)
        newMbr['ready_time']=value

    def slideChangeValue2(self,value):
        self.lbVal2.setText(str(dispTime(value)))
        self.lbVal2.adjustSize()
        newMbr['due_time']=value

    def slideChangeValue3(self,value):
        self.lbVal3.setText(str(dispDuration(value)))
        self.lbVal3.adjustSize()
        newMbr['service_time']=value

def dispTime(tm0):
    t0=tm0*5
    ampm='am'
    if t0>=720:
        ampm='pm'
    
    t1=str(int(t0/60)%12)
    t2=str(t0%60)

    if t1=='0':
        t1='12'
    
    if len(t2)==1:
        t2='0'+t2
    
    t=t1+':'+t2+' '+ampm
    return(t)


def dispDuration(tm0):
    t0=tm0*5
    t1=str(int(t0/60))
    t2=str(t0%60)

    h='hrs'
    m='mins'
    
    if t1=='1':
        h='hr'
    if t2=='1':
        m='min'
    t=t1+' '+h+' '+t2+' '+m  
    return(t)   


class careMans(QWidget):
    def __init__(self,parent=None):
        QWidget.__init__(self, parent)
        layout = QGridLayout()
        
        
        self.lb1=QLabel('Care Manager:')
        self.cmb1=QComboBox()
        
        self.cmb1.activated[str].connect(self.onActivated) 

        layout.addWidget(self.lb1,1,1)
        layout.addWidget(self.cmb1,1,2)
        
        self.setLayout(layout)
    
    def onActivated(self, cm_id):
        tbs.setCMTable(cm_id)
        #print('cal date is:',cal1.selectedDate().toPyDate())

    def addCM(self,cm_list):
        self.cmb1.clear()
        for cm in cm_list:
            self.cmb1.addItem(str(cm[0]))


class tbSched(QWidget):
    def __init__(self,parent=None):
        QWidget.__init__(self, parent)
        layout = QGridLayout()
        
        self.table 	= QTableWidget()
        self.tableItem 	= QTableWidgetItem()
        self.table.verticalHeader().hide()
        # initiate table
        #self.table.setWindowTitle('CARE MANAGER #1')
        #self.table.resize(300, 300)
        self.table.setRowCount(100)
        self.table.setColumnCount(7)
        
        
        # set label
        self.table.setHorizontalHeaderLabels(['Order Ind','Mbr ID','Mbr Name','Mbr Address','Apt Win From','Apt Win To','Apt Length'])
        #table.setVerticalHeaderLabels(QString("V1;V2;V3;V4").split(";"))
 

        self.table.setColumnWidth(0,80)
        self.table.setColumnWidth(1,80)
        self.table.setColumnWidth(2,150)
        self.table.setColumnWidth(3,200)
        self.table.setColumnWidth(4,100)
        self.table.setColumnWidth(5,100)
        self.table.setColumnWidth(6,100)

        self.table.horizontalHeader().setStretchLastSection(True)
        
        
        # on click function
        #self.table.cellClicked.connect(cellClick)
        
        self.CMlb1=QLabel('')
       
        layout.addWidget(self.CMlb1,1,1)
        layout.addWidget(self.table,2,1)
        
        self.setLayout(layout)

    def setCMTable(self,cm_id):
        conn=sqlite3.connect(dtb)
        c=conn.cursor()
        print('CMT IS',cm_id)
        print('cal date is:',cal1.selectedDate().toPyDate())
        svc_dt=cal1.selectedDate().toPyDate()

        self.CMlb1.setText('Care Manager #'+str(cm_id))
        self.CMlb1.adjustSize()

        c.execute('''select a.order_id,
                            a.mbr_id, 
                            b.full_name,
                            b.full_addr,
                            a.svc_tm_from,
                            a.svc_tm_to,
                            a.svc_len
                            
                    from    schedule a,
                            mbrs b
                    where   a.mbr_id = b.mbr_id and
                            cm_id =? and svc_dt =?''',(cm_id,svc_dt,))
        
        recs=c.fetchall()
        for pos in range(len(recs)):
            self.table.setItem(pos,0, QTableWidgetItem(str(recs[pos][0])))
            self.table.setItem(pos,1, QTableWidgetItem(str(recs[pos][1])))
            self.table.setItem(pos,2, QTableWidgetItem(str(recs[pos][2])))
            self.table.setItem(pos,3, QTableWidgetItem(str(recs[pos][3])))
            self.table.setItem(pos,4, QTableWidgetItem(str(dispTime(recs[pos][4]))))
            self.table.setItem(pos,5, QTableWidgetItem(str(dispTime(recs[pos][5]))))
            self.table.setItem(pos,6, QTableWidgetItem(str(dispDuration(recs[pos][6]))))
        conn.close()
       
        blankout_start=len(recs)
        data_pop=True
        while data_pop:
            try:
                table_pop=self.table.item(blankout_start,0).text()
                self.table.setItem(blankout_start,0, QTableWidgetItem(str('')))
                self.table.setItem(blankout_start,1, QTableWidgetItem(str('')))
                self.table.setItem(blankout_start,2, QTableWidgetItem(str('')))
                self.table.setItem(blankout_start,3, QTableWidgetItem(str('')))
                self.table.setItem(blankout_start,4, QTableWidgetItem(str('')))
                self.table.setItem(blankout_start,5, QTableWidgetItem(str('')))
                self.table.setItem(blankout_start,6, QTableWidgetItem(str('')))
                blankout_start+=1
            except:
                data_pop=False

 
        #self.table.setItem(0,0, QTableWidgetItem('hello'))

#def cellClick(row,col):
#    print("Click on " + str(row) + " " + str(col))

def calClick(date):

    sd=date.toPyDate()
    print("Clicked on " + str(sd))
    conn=sqlite3.connect(dtb)
    c=conn.cursor()
    
    c.execute('''select distinct cm_id
                from schedule
                where svc_dt =?''',(sd,))
        
    cm_list=c.fetchall()
    for cm in cm_list:
        print(cm[0])
    
    crm.addCM(cm_list)
    conn.close()

    tbs.setCMTable(1)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('Medica Care Management Scheduler')
   
    layout=QGridLayout()
    
    cal1=QCalendarWidget()
    cal1.clicked[QDate].connect(calClick)
    crm=careMans()
    tbs=tbSched()
    nappt=newAppt()

    layout.addWidget(cal1,1,1,1,1)
    layout.addWidget(nappt,1,2,1,1)
    layout.addWidget(crm,2,1,1,1)
    layout.addWidget(tbs,3,1,1,2)
    
    window.setGeometry(50, 50, 900, 600)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())
