###DATABASES
import pymel.core as pm
import os.path
import os
import copy
import pymel.core.system as pmsys
import pymongo 
import ssl

import publish
reload (publish)

#The global variable for database acess
db = None
currentProject=None

#basic connection
def mongoConnect():
    global db
    pymongo.version
    client = pymongo.MongoClient('localhost', 27017)
    db = client.lcPipeline   
    #return db
    
##Projects
def getDefaultDict():    
    projDict= {'projectName': '',
           'prefix':'',
           'workLocation': u'D:/JOBS/PIPELINE/pipeExemple/scenes',
           'publishLocation': u'D:/JOBS/PIPELINE/pipeExemple/publishes',
           'cacheLocation': u'D:/JOBS/PIPELINE/pipeExemple/cache/alembic',
           'assetCollection': '_asset',
           'shotCollection':  '_shot',
           'status':'active',
           'assetFolders':{'character':'','props':'','sets':'', 'primary':'character'},
           'shotFolders':{},
           'assetNameTemplate':['$prefix','$code','_','$name','_','$task'],
           'cacheNameTemplate':['$prefix','$code','$task'],
           'nextAsset':1,
           'nextShot':1,
           'renderer': 'vray',
           'fps':24,
           'resolution':[1920,1080],
           'workflow':{'rig':{ 'model':{'type':'asset','phase':'preProd', 'short':'mod', 'components':[]},
                               'uvs':{'type':'asset','phase':'preProd','short':'uvs', 'components':[('model', 'import')]},
                               'blendShape':{'type':'asset','phase':'preProd','short':'bsp', 'components':[('model', 'import')]},
                               'texture':{'type':'asset','phase':'preProd','short':'tex', 'components':[('uvs', 'reference')]},
                               'xlo':{'type':'asset','phase':'preProd','short':'xlo', 'components':[('uvs', 'import')]},
                               'rig':{'type':'asset','phase':'preProd','short':'rig', 'components':[('uvs', 'import'),('blendShape', 'import')]}},
                       
                       'static':{  'model':{'type':'asset','phase':'preProd', 'short':'mod', 'components':[]},
                                   'uvs':{'type':'asset','phase':'preProd','short':'uvs', 'components':[('model', 'import')]},                      
                                   'texture':{'type':'asset','phase':'preProd','short':'tex', 'components':[('uvs', 'reference')]}},
                       
                       'shot':{    'layout':{'type':'shot','phase':'prod','short':'lay', 'components':[]},
                                   'animation':{'type':'shot','phase':'prod','short':'ani', 'components':[('layout', 'copy')]},
                                   'render':{'type':'shot','phase':'postProd','short':'rnd', 'components':[('shotFinalizing', 'cache')]},
                                   'shotFinalizing':{'type':'shot','phase':'prod','short':'sfh', 'components':[('animation', 'copy')]}},

                       'shotXlo':{ 'layout':{'type':'shot','phase':'prod','short':'lay', 'components':[]},
                                   'animation':{'type':'shot','phase':'prod','short':'ani', 'components':[('layout', 'copy')]},
                                   'render':{'type':'shot','phase':'postProd','short':'rnd', 'components':[('shotFinalizing', 'xlo')]},
                                   'shotFinalizing':{'type':'shot','phase':'prod','short':'sfh', 'components':[('animation', 'copy')]}},

                       'keyLightShot':{'layout':{'type':'shot','phase':'prod','short':'lay', 'components':[]},
                                   'animation':{'type':'shot','phase':'prod','short':'ani', 'components':[('layout', 'copy')]},
                                   'lighting':{'type':'shot','phase':'postProd','short':'lit', 'components':[('shotFinalizing', 'reference')]},
                                   'render':{'type':'shot','phase':'postProd','short':'rnd', 'components':[('shotFinalizing', 'cache')]},
                                   'shotFinalizing':{'type':'shot','phase':'prod','short':'sfh', 'components':[('animation', 'copy')]}}
                                   }}
    return projDict
    
def addProject (database, **projectSettings):
    projDict= getDefaultDict()
    projDict.update( projectSettings )                                                           
    database.create_collection ( projectSettings['projectName']+'_asset' )   
    database.create_collection ( projectSettings['projectName']+'_shot' )     
    database.projects.insert_one( projDict )

def editProject (database,projectName, **projectSettings):
    projDict= getDefaultDict()                                       
    projDict.update( projectSettings )
    database.projects.find_one_and_update( {'projectName':projectName}, {'$set':projDict} )    


##DATABASE
def getItemMData(projName = None, task = None, code = None, type = None, fromScene = False):
    global db
    global currentProject

    if fromScene:
        projName = pm.fileInfo.get('projectName')
        task = pm.fileInfo.get('task')
        code = pm.fileInfo.get('code')
        type = pm.fileInfo.get('type')

        if not projName or not task or not code or not type:
            print 'ERROR getItemData: Cant get item Metadata. Scene has incomplete fileInfo:', projName, task, code, type

    else:
        if not task or not code:
            print 'ERROR getItemData: Cant get item Metadata. Missing item ids on function call:', projName, task, code, type
        
        if not projName:
            projName = currentProject
        
        if not type:
            type = getTaskType(task)
            print 'WARNING getItemData: getting type from task', task, type

    collection = db.get_collection (projName+'_'+type)
    item = collection.find_one ({'task':task, 'code':code})

    if not item:
        print 'ERROR getItemData: Cant find item Metadata on database:', projName, task, code, type

    return item

def putItemMData(item, projName = None, task = None, code = None, type = None, fromScene = True):
    global db
    global currentProject

    if not item:
        print 'ERROR putItemData: no item metadata in function call:'

    if fromScene:
        projName = pm.fileInfo.get('projectName')
        task = pm.fileInfo.get('task')
        code = pm.fileInfo.get('code')
        type = pm.fileInfo.get('type')

        if not projName or not task or not code or not type:
            print 'ERROR putItemData: Cant put item Metadata. Scene has incomplete fileInfo:', projName, task, code, type
            return
    else:
        if not task or not code:
            print 'ERROR putItemData: Cant get item Metadata. Missing item ids on function call:', projName, task, code, type
        
        if not projName:
            projName = currentProject
        
        if not type:
            type = getTaskType(task)
            print 'WARNING putItemData: getting type from task', task, type

    collection = db.get_collection (projName+'_'+type)
    item = collection.find_one_and_update ({'task':task, 'code':code }, {'$set':item})

    return item

##NAMEPROCESS
def templateName(item, template=None):
    global db
    global currentProject

    proj = db.projects.find_one ({'projectName':currentProject})

    if template:
        itemNameTemplate = template
    else:
        type = item['type']

        if type == 'asset' or type == 'shot':       
            itemNameTemplate = proj['assetNameTemplate']
        elif type == 'cache':
            itemNameTemplate = proj['cacheNameTemplate'] 
                  
    taskShort= getTaskShort(item['task'])
    code=item['code']
    name=item['name']  
    prefix=proj['prefix']
    
    fileNameList = itemNameTemplate
    fileNameList = [taskShort if x=='$task' else x for x in fileNameList]
    fileNameList = [code if x=='$code' else x for x in fileNameList]
    fileNameList = [name if x=='$name' else x for x in fileNameList]
    fileNameList = [prefix if x=='$prefix' else x for x in fileNameList]
    
    fileName = ''.join(fileNameList)
  
    return fileName

def untemplateName(source, template=None):
    global db
    global currentProject

    proj = db.projects.find_one ({'projectName':currentProject})

    if template:
        itemNameTemplate = template
    else:        
        sourceExt = os.path.splitext(source)[1]  

        if sourceExt =='abc' or sourceExt =='.abc':       
            itemNameTemplate = proj['cacheNameTemplate']
        else:
            itemNameTemplate = proj['assetNameTemplate'] 
            
    sourceName= os.path.splitext(source)[0]

    if '$name' in itemNameTemplate:        
        nameId = itemNameTemplate.index('$name')
        templateStart = itemNameTemplate[ :nameId]
        templateEnd = itemNameTemplate[ nameId+1:]
    else:
        templateStart = itemNameTemplate
        templateEnd = None

    separators = {}
    prefix = None
    task = None
    code = None
    name = None
            
    for p in itemNameTemplate:
        if (p!='$prefix') and (p!='$code') and (p!='$task') and (p!='$name'):
            separators[p]=len(p)
    
    pos=0

    for i,val in enumerate(templateStart): 
        if val == '$prefix':
            prefix = sourceName[pos:pos+2]
            pos = pos+2
        elif val == '$code':
            code = sourceName[pos:pos+4]
            pos = pos+4
        elif val == '$task':
            task = sourceName[pos:pos+3]
            pos = pos+3      
        else:
            pos = pos+separators[val] 

    posStart=pos    
    pos=len(sourceName)

    if templateEnd:
        for i,val in enumerate(reversed(templateEnd)): 
            if val=='$prefix':
                prefix=sourceName[pos-2:pos]
                pos=pos-2
            elif val=='$code':
                code=sourceName[pos-4:pos]
                pos=pos-4
            elif val=='$task':
                task=sourceName[pos-3:pos]
                pos=pos-3       
            else:
                pos=pos-separators[val]
            
    posEnd=pos
    name = sourceName[posStart:posEnd] 

    return  prefix,task,code,name
                 
## CREATE ASSET!! 
def incrementNextCode(type, fromBegining=False):
    global db
    global currentProject

    flag=True
    proj = db.projects.find_one ({'projectName':currentProject})
    collection =  db.get_collection (proj['projectName']+'_'+type)

    if fromBegining:
        nextCode=1
    else:
        nextCode = int (proj['next'+type.capitalize()])        
    
    count = 0
    
    while flag:
        nextCode+=1
        count += 1
        search =  "%04d" % nextCode
        result = collection.find ({'code': search})
        codeExists = [x for x in result] 
    
        if not codeExists:
            flag = False
        if count==150:
            flag=False
    
    db.projects.find_one_and_update ({'projectName':currentProject}, {'$set':{'next'+type.capitalize():nextCode} })                              

         
def createItem(type, name, path, workflow, code=None):
    global db
    global currentProject

    proj = db.projects.find_one ({'projectName':currentProject})
    collection =  db.get_collection (proj['projectName']+'_'+type)

    if code:
        code = ("%04d" % int(code))
        next = False
        result = collection.find ({'code': code })
        codeExists = [x for x in result]
        
        if codeExists:
            return 'codeExists'
        else:
            nextCode = "%04d" % proj['next'+type.capitalize()] 
            if code == nextCode:
                next = True
    else: 
        next = True           
        code = "%04d" % proj['next'+type.capitalize()]

    itemWorkflow = proj['workflow'][workflow]
    itemsDict = {}

    for task, value in itemWorkflow.iteritems():
        itemsDict[task] = { 'name': name,
                            'code': code, 
                            'task': task,
                            'type': type ,
                            'workflow': workflow,
                            'projPrefix':proj['prefix'],
                            'workVer': 0 , 
                            'publishVer': 0, 
                            'path': path, 
                            'filename': 'tmp',
                            'status': 'notCreated',
                            'components':{} } 
                            
        fileName = templateName(itemsDict[task]) 
        itemsDict[task]['filename']=fileName
        
    for task, value in itemWorkflow.iteritems():             
        for component in value['components']:      
            itemsDict[task]['components'][component[0]]= { 'code': itemsDict[component[0]]['code'],
                                                           'ver':1 ,
                                                           'updateMode':'last',
                                                           'task':component[0],
                                                           'assembleMode': component[1],
                                                           'type': itemsDict[component[0]]['type'] }
                                                     
    list = [x for x in itemsDict.itervalues()]
    collection.insert_many(list)    
    incrementNextCode(type, fromBegining = not next) 
     
    return  itemsDict 

def removeItem(type, code):
    global db
    global currentProject

    print 'remove item'
    collection =  db.get_collection (currentProject+'_'+type)   
    rem = collection.delete_many({'code': code})
        
##Items 
def addComponent(item, ns, componentTask , componentCode, assembleMode): 
    global db
    global currentProject

    type = getTaskType(componentTask)
    compCollection = db.get_collection (currentProject+'_'+type)
    componentMData = compCollection.find_one ({'task':componentTask, 'code':componentCode}) ##hardcode so assets
    componentDict = {  'code': componentCode,
                       'ver':1 ,
                       'updateMode':'last',
                       'task':componentTask,
                       'assembleMode': assembleMode,
                       'type': componentMData['type'] } 
    nsList = item['components'].keys() 
    index = 1
    nsBase = ns

    while ns in nsList:
        ns = nsBase+str(index)
        index+=1
    
    itemCollection = db.get_collection (currentProject+'_'+item['type'])    
    item['components'][ns]=  componentDict           
    result = itemCollection.find_one_and_update( {'task':item['task'], 'code':item['code']} , {'$set' :item}  )

    return result

def removeComponent(item, ns):
    global db
    global currentProject

    del item['components'][ns]
    collection = db.get_collection (currentProject+'_'+item['type'])    
    collection.find_one_and_update( {'task':item['task'], 'code':item['code']} , {'$set' : item}  )

###ASSEMBLE
def find(code, task, collection): ##decrapted!!
    item = collection.find_one ({'task':task, 'code':code}) 

    if item:
        return item
    else:
        print 'FIND: item not found'
        return        

def getTaskType(task) : 
    global db
    global currentProject   
    
    proj = db.projects.find_one ({'projectName':currentProject})

    if task=='asset' or task=='shot':
        return task 
             
    resultTasks=[]

    for workflow in proj['workflow'].itervalues():
        for key, values in workflow.iteritems():
            if key == task:    
                resultTasks.append (values['type'])

    if resultTasks: 
        return resultTasks[0]
    else:
        print 'ERROR getTaskType: no task type found!'

def getTaskLong(taskShort):
    global db
    global currentProject

    project = db.projects.find_one ({'projectName':currentProject})

    result=[]
    for workflow in project['workflow'].itervalues():
        for key, value in workflow.iteritems():
            if value['short']==taskShort:
                result.append(key)
    if result:
        return result[0]
    else:
        print 'ERROR getTaskLong: no long name for this task short!'

def getTaskShort(taskLong):  
    global db
    global currentProject 

    project = db.projects.find_one ({'projectName':currentProject})

    result=[]
    for workflow in project['workflow'].itervalues():
        for key, values in workflow.iteritems():
            if key == taskLong:    
                result.append (values['short'])
    if result:
        return result[0]
    else:
        print 'ERROR: no short name for this task!'
       
def referenceInfo(refFile):
    fileName = os.path.basename(refFile.path).split('_',1)
    ver = int (fileName[0][1:])
        
    info = untemplateName(fileName[1])
    task = getTaskLong(info[1])
    code = info[2]
    return {'ver':ver, 'task': task, 'code':code}
    
def getPath(item, location='workLocation', ext='ma'):
    global db
    global currentProject

    project = db.projects.find_one ({'projectName':currentProject})

    location = project[location]
    taskFolder = item['task']
    folderPath = os.path.join(*item['path'])
    phase=project['workflow'][item['workflow']][item['task']]['phase']    
    filename = item['filename']

    if ext:
        ext= '.'+ext

    else:
        ext=''

    dirPath =  os.path.join(location, phase, taskFolder, folderPath)
    filename =  filename+ext

    return dirPath, filename  

def open(type,task,code):
    global db
    global currentProject

    collection = db.get_collection (currentProject+'_'+type)
    item = collection.find_one ({'task':task, 'code':code}) 

    if not item:
        print 'ERROR: No metadata for this item'
        return
               
    ## get path
    path = getPath(item)
    sceneDirPath = path[0]
    sceneFullPath = os.path.join (*path)
    
    ## open maya scene
    pm.openFile (sceneFullPath, f=True)

class PublishWidget (publish.PublishWidget):
    def __init__(self, task, code, type):
        super(PublishWidget, self).__init__(task)

        self.task = task
        self.code = code
        self.type = type

    def publishFile (self, *args):
        global db
        global currentProject

        #get database info on item
        collection = db.get_collection (currentProject+'_'+ self.type )   
        item = getItemMData(task = self.task, code = self.code, type = self.type)
        #get path
        originalName = pm.sceneName ()
        path = getPath(item, location='publishLocation')
        dirPath = path[0]
        filename = path[1]    

        # increment publish version
        item['publishVer']+=1
        collection.find_one_and_update({'task':self.task, 'code':self.code} , {'$set' : {'publishVer':item['publishVer'] }} )
        publishVer = 'v%03d_' %  item['publishVer']    

        #make full path 
        fullPath =  os.path.join( dirPath, publishVer + filename) 

        if not os.path.exists(dirPath): 
            print ('creating:' + dirPath)
            os.makedirs(dirPath)

        print 'publish ver %s, at %s' % (publishVer, fullPath) 

        # save scene
        pm.saveAs ( fullPath )
        pm.renameFile ( originalName )
        self.closeWin()

def publish(type,  task, code) :             
    pubWidget = PublishWidget (task=task, code=code, type=type)
    pubWidget.createWin()

    
def cachePrompt(refs):
    form = pm.setParent(q=True)
    pm.formLayout(form, e=True, width=300)
    t = pm.text(l='geo groups to cache')
    t2 = pm.text(l='change selection')
    b3 = pm.button(l='Cancel', c='pm.layoutDialog( dismiss="Abort" )' )
    #b2 = pm.button(l='Cancel', c='pm.layoutDialog( dismiss="Cancel" )' )
    b1 = pm.button(l='OK', c=lambda x:cachePromptChangeList() )
    cb1 = pm.textScrollList('cacheScrollList', allowMultiSelection=True, si=refs, append=refs )
    spacer = 5
    top = 5
    edge = 5
    pm.formLayout(form, edit=True, attachForm=[(cb1, 'right', edge),(t, 'top', top), (t, 'left', edge), (t, 'right', edge),
                                               (t2, 'left', edge), (t2, 'right', edge), (b1, 'left', edge), (b1, 'bottom', edge), 
                                               (b3, 'bottom', edge), (b3, 'right', edge), (cb1, 'left', edge)],
                                                
                                    attachNone=[(t, 'bottom')],
                                    attachControl=[(cb1, 'top', spacer,t2),(t2, 'top', spacer,t)],
                                    attachPosition=[(b1, 'right', spacer, 33), (b3, 'left', spacer, 66)])

def cachePromptChangeList(*args):
    sel = pm.textScrollList('cacheScrollList', q=True, si=True)  
    selString = ','.join(sel)
    print selString
    pm.layoutDialog( dismiss = selString ) 
                                       
def cacheScene(task, code):
    global db
    global currentProject

    collection = db.get_collection (currentProject+'_shot')
    shotMData = getItemMData(task = task, code = code, type = 'shot')
        
    if not 'caches' in shotMData:
        shotMData['caches'] = copy.deepcopy(shotMData['components'])

        for item in shotMData['caches'].itervalues(): 
            item['ver']=0   
            item['type']='cache'
            item['assembleMode']='cache'
            item['sourceSceneVer']=0
            item['sourceVer']=0
            item['name']=''
                 
    itemComponents = shotMData ['components']           
    itemCaches = shotMData['caches']
    geoGroups = pm.ls ('geo_group', r=True)

    choosen = pm.layoutDialog(ui=lambda :cachePrompt(geoGroups)) 

    if 'Abort' in choosen:
        return
   
    path = getPath(shotMData, location='cacheLocation', ext='')
    cachePath = os.path.join (*path)
    
    if not os.path.exists(cachePath):
        os.makedirs(cachePath)

    choosenGeoGroups = [pm.PyNode (x) for x in choosen.split (',')]   

    for geoGroup in choosenGeoGroups:         
        #get all geometry on geo_group   
        geosShape = geoGroup.getChildren(allDescendents=True, type='geometryShape')
        geos=[x.getParent() for x in geosShape]    
        jobGeos=''   

        # make path and name for alembic file  
        ns = geoGroup.namespace()[:-1]        
        cacheMData=itemCaches[ns] # get the data for this component 

        #get version and increment            
        cacheMData['ver'] += 1
        cacheMData['sourceSceneVer'] = shotMData['publishVer']
        cacheMData['sourceVer'] = itemComponents[ns]['ver']
         
        ver = cacheMData['ver']

        #get cache publish path    

        cacheName = templateName(cacheMData)+'_'+ns          
        cacheFileName = str('v%03d_' % ver) + cacheName
        cacheFullPath = os.path.join (cachePath,cacheFileName) 

        jobFile = " -file "+cacheFullPath+".abc "       

        #get scene frame range        
        ini = str(int( pm.playbackOptions (q=True, min=True)))
        fim = str(int( pm.playbackOptions (q=True, max=True)))
        jobFrameRange = ' -frameRange '+ini+' '+fim        

        # set parameters for alembic cache     
        jobAttr = " -attr translateX -attr translateY -attr translateZ -attr rotateX -attr rotateY -attr rotateZ -attr scaleX -attr scaleY -attr scaleZ -attr visibility"
        jobOptions =" -worldSpace -uv -writeVisibility"  

        # assemble cache arguments
        jobArg  = jobFrameRange+jobOptions+jobAttr+jobGeos+jobFile  

        # do caching
        pm.AbcExport (j =jobArg)
    
    collection.find_one_and_update({'task':task, 'code':code} , {'$set' : shotMData } )

    pm.confirmDialog( title='cache',ma='center',icon='information', message='Cache Ver: %s' % (ver), button=['OK'], defaultButton='OK', dismissString='ok')

def referenceCache(componentMData):
    path = getPath(componentMData, location='cacheLocation', ext='')
    cachePath = os.path.join (*path)

    for cache_ns, cacheMData in componentMData['caches'].iteritems():
        if cacheMData['ver']==0:
            print 'Component %s not yet published!!' % (cache_ns+':'+cacheMData['task']+cacheMData['code'])
            parcial=True
            continue 

        ver = 'v%03d_' % cacheMData['ver']  
        cacheName = templateName(cacheMData)+'_'+cache_ns                                          
        cacheFileName = ver+cacheName+'.abc'
        cacheFullPath = os.path.join (cachePath,cacheFileName)

        pm.createReference (cacheFullPath, namespace=cache_ns, groupReference=True, groupName='geo_group', type='Alembic')
        #pm.rename (component_ns+':geo_group', cache_ns+':geo_group')    


def importCaches(componentMData):
    path = getPath(componentMData, location='cacheLocation', ext='')
    cachePath = os.path.join (*path)

    for cache_ns, cacheMData in componentMData['caches'].iteritems():
        if cacheMData['ver']==0:
            print 'Component %s not yet published!!' % (cache_ns+':'+cacheMData['task']+cacheMData['code'])
            parcial=True
            continue 

        ver = 'v%03d_' % cacheMData['ver']  
        cacheName = templateName(cacheMData)+'_'+cache_ns                                          
        cacheFileName = ver+cacheName+'.abc'
        cacheFullPath = os.path.join (cachePath,cacheFileName)

        pm.AbcImport (cacheFullPath, mode='import', fitTimeRange = True, setToStartFrame = True, connect = '/' )
        #pm.rename (component_ns+':geo_group', cache_ns+':geo_group')    

    return 

def referenceXlos(componentMData):
    for ns, xlo in componentMData['components'].iteritems():
        xloMData = getItemMData(task = 'xlo', code = xlo['code'], type =xlo['type'])
        path = getPath(xloMData, location='publishLocation')

        for xlo_ns, xloMData in componentMData['caches'].iteritems():
            if xloMData['ver']==0:
                print 'Component %s not yet published!!' % (xlo_ns+':'+xloMData['task']+xloMData['code'])
                parcial=True
                continue 

            else:

                version = 'v%03d_' % xloMData['publishVer']

        xloPath = os.path.join( path[0] , version + path[1])

        pm.importFile (xloPath, namespace=ns)        
    
def assemble(type, task, code):   
    global db
    global currentProject
    empty=True
    parcial=False
    fromSource = False
    
    print 'start assembling'

    ## read from database
    collection = db.get_collection (currentProject+'_'+type)
    itemMData = getItemMData(task = task, code = code, type = type) 

    if not itemMData:
        print 'ERROR: No metadata for this item'
        return

    pm.newFile (f = True, new=True)

    if 'source' in itemMData:
        fromSource = True
        itemComponents = itemMData['source']
    else:
        itemComponents = itemMData['components']


    for component_ns, component in itemComponents.iteritems():
        ## read components item    
        componentMData = getItemMData(code=component['code'], task=component['task'], type=component['type'])  

        if not componentMData:
            print 'ignoring...'
            continue

        if componentMData['publishVer']==0:
            print 'Component %s not yet published!!' % (component_ns+':'+component['task']+component['code'])
            parcial=True
            continue


        path = getPath(componentMData, location='publishLocation')
        version = 'v%03d_' % componentMData['publishVer']   
        componentPath =  os.path.join( path[0] , version + path[1])             

        empty=False  
          
        ## use caches
        if component['assembleMode']=='cache':
 
            pm.namespace( add=component_ns)
            pm.namespace( set=component_ns)
           
            referenceCache(componentMData)
  
            if not fromSource:
                itemMData['source']=copy.deepcopy(itemMData['components'])

            itemMData['components']=copy.deepcopy(componentMData['caches'])

            pm.namespace( set=':')

        ## xlo
        elif component['assembleMode']=='xlo':
            #pm.namespace( add=component_ns)
            #pm.namespace( set=component_ns)
            referenceXlos(componentMData)
            importCaches(componentMData)

            if not fromSource:
                itemMData['source']=copy.deepcopy(itemMData['components'])

            itemMData['components']=copy.deepcopy(componentMData['components'])
            #pm.namespace( set=':')

        ## import
        elif component['assembleMode']=='import':
            pm.importFile (componentPath, defaultNamespace=True)   

        ## reference 
        elif component['assembleMode']=='reference':        
            ns = component_ns
            pm.createReference (componentPath, namespace=ns)

        ## copy from another scene
        elif component['assembleMode']=='copy':   
            pm.openFile (componentPath, force=True)

            if not fromSource:
                itemMData['source']=copy.deepcopy(itemMData['components'])

            itemMData['components']=copy.deepcopy(componentMData['components'])                
            #pm.renameFile ( sceneFullPath )
            
    ## update infos on scene and database                
    if not empty or not itemComponents:
        pm.fileInfo['projectName'] = currentProject
        pm.fileInfo['task'] = itemMData['task']
        pm.fileInfo['code'] = itemMData['code']
        pm.fileInfo['type'] = itemMData['type'] 
        itemMData['workVer']=1 
        itemMData['status']='created'
        collection.find_one_and_update({'task':task, 'code':code} , {'$set' : itemMData } )
    
        itemPath = getPath(itemMData)
        sceneDirPath = itemPath[0]
        sceneFullPath = os.path.join (*itemPath) 

        if not os.path.exists(sceneDirPath):
            os.makedirs(sceneDirPath)

        pm.saveAs ( sceneFullPath )             
    
        if parcial:
            print 'WARNING assemble: Some components have no publish to complete assemble this file!'

        else:
            print '%s assembled sucessfully!' % itemMData['filename']     
        
    else:
        print 'ERROR assemble: No component published to assemble this file'        

##SCENE CHECK
def confirmPopUp(msg):
     return pm.confirmDialog( title='PopUp',ma='center', message=msg, button=['OK', 'Cancel'], defaultButton='OK', dismissString='Cancel')   

def refCheckPrompt(refs, type):
    form = pm.setParent(q=True)
    pm.formLayout(form, e=True, width=300)
    t = pm.text(l='this references are marked to %s' % type)
    t2 = pm.text(l='change selection')
    b3 = pm.button(l='Cancel', c='pm.layoutDialog( dismiss="Abort" )' )
    #b2 = pm.button(l='Cancel', c='pm.layoutDialog( dismiss="Cancel" )' )
    b1 = pm.button(l='OK', c=lambda x:changeList() )
    cb1 = pm.textScrollList('scrollList', allowMultiSelection=True, si=refs, append=refs )
    spacer = 5
    top = 5
    edge = 5
    pm.formLayout(form, edit=True, attachForm=[(cb1, 'right', edge),(t, 'top', top), (t, 'left', edge), (t, 'right', edge),
                                               (t2, 'left', edge), (t2, 'right', edge), (b1, 'left', edge), (b1, 'bottom', edge), 
                                               (b3, 'bottom', edge), (b3, 'right', edge), (cb1, 'left', edge)],
                                                
                                    attachNone=[(t, 'bottom')],
                                    attachControl=[(cb1, 'top', spacer,t2),(t2, 'top', spacer,t)],
                                    attachPosition=[(b1, 'right', spacer, 33), (b3, 'left', spacer, 66)])

def changeList(*args):
    sel = pm.textScrollList('scrollList', q=True, si=True)  
    selString = ','.join(sel)
    pm.layoutDialog( dismiss=selString ) 
    
## replace ref
def replaceRef(wrongRef):
    global db
    global currentProject

    projName = pm.fileInfo.get('projectName')
    if currentProject != projName:
        print 'ERROR replaceRef: This file is from a project different from the current project'
        return

    item = getItemMData(fromScene=True)
    components=item['components']
    refOnSceneList = pm.getReferences()
    
    for component_ns in wrongRef:
        ref=refOnSceneList[component_ns]         
        component=components[component_ns] 
                   
        if component['assembleMode']=='reference':   
            componentMData = getItemMData(code=component['code'], task=component['task'], type = component['type'] )

            if componentMData['publishVer']==0:
                print 'Component %s not yet published!!' % (component_ns+':'+component['task']+component['code'])
                continue

            else:
                version = 'v%03d_' % componentMData['publishVer'] 
            
            path = getPath(componentMData, location='publishLocation') 
            componentPath =  os.path.join( path[0] , version + path[1])  
            ref.replaceWith(componentPath)
            
        elif component['assembleMode']=='cache':            
            source = [x for x in item['source'].itervalues()][0]
            componentMData = getItemMData (code=source['code'], task=source['task'], type = source['type'])

            path = getPath(componentMData, location='cacheLocation', ext='')
            name=path[1]
            cachePath = os.path.join (*path)
            #pm.namespace( set=':'+componentMData['task'])
            
            cache_ns = component_ns
            cache = componentMData['caches'][cache_ns]

            if cache['ver']==0:
                print 'Component not yet published!!'
                continue

            else:
                ver = 'v%03d_' % cache['ver']  
             
            cacheName = templateName(cache)+'_'+cache_ns                                          
            cacheFileName = ver+cacheName+'.abc'
            cacheFullPath = os.path.join (cachePath,cacheFileName)
             
            ref.replaceWith(cacheFullPath)
                        
def delRef(refToDelete):
    refOnSceneList = pm.getReferences()
    item = getItemMData(fromScene=True)
    components=item['components']

    for ns in refToDelete:
        ref=refOnSceneList[ns]
        print 'WARNING: Removing reference %s' % os.path.basename (ref.path)
        ref.remove()

## add ref
def addRef(refToAdd):
    global db
    global currentProject

    projName = pm.fileInfo.get('projectName')
    if currentProject != projName:
        print 'ERROR addRef: This file is from a project different from the current project'
        return

    item = getItemMData(fromScene=True)
    components = item['components'] 

    for component_ns in refToAdd:
        component = components[component_ns]

        if component['type'] == 'cache':
            source = [x for x in item['source'].itervalues()][0]
            componentMData = getItemMData(code=source['code'], task=source['task'], type = source['type'])
            
            path = getPath(componentMData, location='cacheLocation', ext='')
            name = path[1]
            cachePath = os.path.join (*path)

            pm.namespace( set=':'+componentMData['task'])
            
            cache_ns = component_ns
            cache = componentMData['caches'][cache_ns]

            if cache['ver']==0:
                print 'Component not yet published!!'
                continue

            else:
                ver = 'v%03d_' % cache['ver']  
             
            cacheName = templateName(cache)+'_'+cache_ns                                          
            cacheFileName = ver+cacheName+'.abc'
            cacheFullPath = os.path.join (cachePath,cacheFileName)
            pm.createReference (cacheFullPath, namespace=cache_ns, groupReference=True, groupName='geo_group', type='Alembic')
            pm.rename (componentMData['task']+':geo_group', cache_ns+':geo_group')  

            pm.namespace( set=':')

        else:
            componentMData = getItemMData(code=component['code'], task=component['task'], type = component['type'] ) 

            if componentMData['publishVer']==0:
                print 'Component %s not yet published!!' % (component_ns+':'+component['task']+component['code'])
                continue

            else:
                version = 'v%03d_' % componentMData['publishVer']               
    
            #use files            
            path = getPath(componentMData, location='publishLocation') 
            componentPath =  os.path.join( path[0] , version + path[1])  

            ## import               
            if component['assembleMode']=='import':
                pm.importFile (componentPath, defaultNamespace=True) 

            ## reference 
            elif component['assembleMode']=='reference':        
                ns = component_ns
                pm.createReference (componentPath, namespace=ns)

            ## copy from another scene
            elif component['assembleMode']=='copy':   
                pm.openFile (componentPath, force=True)
                item['source']=copy.deepcopy(item['components'])
                item['components']=copy.deepcopy(componentMData['components'])
                pm.saveAs ( sceneFullPath )
            
## version updated
def checkVersions():
    global db
    global currentProject

    projName = pm.fileInfo.get('projectName')
    if currentProject != projName:
        print 'ERROR checkVersions: This file is from a project different from the current project'
        return

    item = getItemMData(fromScene = True)
    components=item['components']

    for component_ns, component in components.iteritems():
        
        if component['type']=='cache':
            source=[x for x in item['source'].itervalues()][0]
            componentMData = getItemMData(code=source['code'], task=source['task'], type = source['type'])

            if not componentMData:
                print 'missing data for %s : %s %s' % (component_ns, component['task'], component['code'])
                print 'ignoring...'
                continue

            cache_ns = component_ns
            cache = componentMData['caches'][cache_ns]

            if cache['ver']==0:
                print 'Component not yet published!!'
                continue

            else:
                if component['ver'] != cache['ver']:
                    component['ver'] = cache['ver']         
                    print 'Component %s version updated to %d' % ((component_ns+':'+component['task']+component['code']), cache['ver'])

                else:
                    print 'Component %s version ok' % (component_ns+':'+component['task']+component['code'])

        else:  
            componentMData = getItemMData(code=component['code'], task=component['task'], type = component['type'] )
            
            if not componentMData:
                print 'missing data for %s : %s %s' % (component_ns, component['task'], component['code'])
                print 'ignoring...'
                continue

            if componentMData['publishVer'] != 0:
                if  component['updateMode']=='last':        
                    component['ver'] = componentMData['publishVer']
                    print 'Component %s version updated to %d' % ((component_ns+':'+component['task']+component['code']), componentMData['publishVer'])

                else:
                    component['ver'] = int(component['updateMode'])

            else:
                print 'Component %s not yet published!!' % (component_ns+':'+component['task']+component['code'])
                continue
    
    putItemMData(item)                                                


def updateRefVersion(refToVerUpdate):
    global db
    global currentProject

    projName = pm.fileInfo.get('projectName')
    if currentProject != projName:
        print 'ERROR checkVersions: This file is from a project different from the current project'
        return


    item = getItemMData(fromScene = True)
    components=item['components']
    refOnSceneList = pm.getReferences()

    for component_ns in refToVerUpdate:
        ref=refOnSceneList[component_ns]    
        component=components[component_ns]
        
        if component['assembleMode']=='reference':
            componentMData = getItemMData(code=component['code'], task=component['task'], type = component['type'] )

            ver = 'v%03d_' % component['ver'] 
            path = getPath(componentMData, location='publishLocation') 
            componentPath =  os.path.join( path[0] , ver + path[1])  
            ref.replaceWith(componentPath)
        
        elif component['assembleMode']=='cache':
            source=[x for x in item['source'].itervalues()][0]
            componentMData = getItemMData(code=source['code'], task=source['task'], type = source['type'])

            path = getPath(componentMData, location='cacheLocation', ext='')
            name=path[1]
            cachePath = os.path.join (*path)
            cache_ns =component_ns
            cache = componentMData['caches'][cache_ns]
            ver = 'v%03d_' % cache['ver']
            cacheName = templateName(cache)+'_'+cache_ns                                          
            cacheFileName = ver+cacheName+'.abc'
            cacheFullPath = os.path.join (cachePath,cacheFileName)
            ref.replaceWith (cacheFullPath)


def sceneRefCheck():
    global db
    global currentProject

    projName = pm.fileInfo.get('projectName')
    if currentProject != projName:
        print 'ERROR sceneRefCheck: This file is from a project different from the current project'
        return

    checkVersions()  
    ## get scene name and item 
    item = getItemMData(fromScene = True)        
        
    components=item['components']
    
    hasRefsOrCaches = [x for x in components if (components[x]['assembleMode']=='reference' or components[x]['assembleMode']=='cache')]
    if not hasRefsOrCaches:
        return
    
    updated=True
  
    #get reference list and components on item
    refOnSceneList = pm.getReferences()
    
    #Check consistency:
    refToAdd = [x for x in components if not x in refOnSceneList]

    if refToAdd:
        mode = 'add'
        x = pm.layoutDialog(ui=lambda :refCheckPrompt(refToAdd, mode))
        updated=False

        if x != 'Abort':
            refToAdd = x.split (',')
            addRef(refToAdd)
            updated=False
                
    refToDelete = [x for x in refOnSceneList if x not in components]

    if refToDelete:
        mode = 'delete'
        x = pm.layoutDialog(ui=lambda :refCheckPrompt(refToDelete, mode))
        updated=False

        if x != 'Abort':
            refToDelete = x.split (',')
            delRef(refToDelete)
            updated=False
        
    wrongRef = [x for x in components if x not in refToAdd and x not in refToDelete and (components[x]['code'] != referenceInfo(refOnSceneList[x])['code'] or components[x]['task'] != referenceInfo(refOnSceneList[x])['task'])]
    
    for x in components:
        print referenceInfo(refOnSceneList[x])
        
    if  wrongRef:
        mode = 'wrong'
        x = pm.layoutDialog(ui=lambda :refCheckPrompt(wrongRef, mode))
        updated=False

        if x != 'Abort':
            wrongRef = x.split (',')
            replaceRef(wrongRef)

        
    refToVerUpdate = [x for x in components if x not in refToAdd and x not in refToDelete and x not in wrongRef and components[x]['ver'] != referenceInfo(refOnSceneList[x])['ver'] ]
    
    if  refToVerUpdate:
        mode = 'update Version'
        x = pm.layoutDialog(ui=lambda :refCheckPrompt(refToVerUpdate, mode))
        updated=False

        if x != 'Abort':
            refToVerUpdate = x.split (',')
            updateRefVersion(refToVerUpdate)

    if updated:
        print 'Scene References OK!!'
            
### INTERFACE
class ItemWidget(object):
    def __init__ (self, name, imgPath, label , parentWidget, color = (0,.2,.50)):
        self.widgetName = None
        self.parentWidget= parentWidget
        
        self.infoWidget= None 
                        
        self.name = name
        self.label = label
        self.imgPath = imgPath
        self.color = color
        
        self.selected = False
        self.task = None
        self.code = None
        self.publishVer = 0
        self.workVer = 0
        
    def getItem(self):
        global db
        projName = self.parentWidget.projectName
        type = getTaskType(self.task)
        collection = db.get_collection( projName+'_'+type )
        if self.task=='asset':
            searchTask='model'
        elif self.task=='shot':
            searchTask='layout'
        else:
            searchTask=self.task
           
        item = collection.find_one ({'task':searchTask, 'code':self.code})
        return item
                         
    def dClickCallBack(self, *args):        
        if self.task=='asset' or self.task=='shot':
            self.parentWidget.refreshList(path=self.parentWidget.path, task=self.task, code=self.code)  
              
    def clickCallBack(self, *args):
        if self.selected:
            pm.iconTextButton( self.name , e=True,  backgroundColor=self.color )
            self.parentWidget.selectedItem = None
            self.selected = False 
        else:
            if self.parentWidget.selectedItem:            
                pm.iconTextButton( self.parentWidget.selectedItem.name , e=True,  backgroundColor=self.parentWidget.selectedItem.color )
                self.parentWidget.selectedItem.selected= False
            pm.iconTextButton( self.name , e=True,  backgroundColor=(.27,.27,.27) )
            self.parentWidget.selectedItem = self
            self.selected = True
            if self.infoWidget:  
                self.infoWidget.putInfo(self)
    
    def dragCallback(self, dragControl, x, y, modifiers):
        return [self.task, self.code] 
            
    def removeCallback (self,*args):
        print 'remove Item'
        projName = self.parentWidget.projectName
        type = getTaskType(self.task)
        removeItem(type, self.code)
        pm.evalDeferred( 'cmds.deleteUI("'+self.widgetName+'")')
        self.parentWidget.itemList.remove(self)
                
    def openCallback(self,*args):
        print 'open'
        projName = self.parentWidget.projectName
        item = self.getItem()
        if item['status']=='notCreated':
            return pm.confirmDialog( title='error',ma='center', message='This scene is not assembled yet', button=['OK'], defaultButton='OK', dismissString='OK')            
        open(type = item['type'],task = item['task'],code = item['code'])
        
    def assembleCallback(self,*args):
        print 'assemble'        
        projName = self.parentWidget.projectName
        item = self.getItem()
        type = getTaskType(self.task)
        if  item['status']=='notCreated':
            assemble(type ,self.task,self.code)
        else:
            resp = pm.confirmDialog( title='Confirm', message='This item is already assembled \n Do you want to reassemble?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )    
            if resp=='Yes':
                assemble(type ,self.task,self.code)    
        
    def shotManagerCallback(self,*args):
        item = self.getItem()
        shotMng = ShotManager(item)
        shotMng.projectName =self.parentWidget.projectName
        shotMng.createShotManager()
                              
    def addToLayout(self):
        self.widgetName = pm.iconTextButton( self.name,  p= self.parentWidget.widgetName ,backgroundColor=self.color,  style='iconAndTextHorizontal', image=self.imgPath, label=self.label ,h=100, w=220, doubleClickCommand=self.dClickCallBack, command=self.clickCallBack , dragCallback = self.dragCallback )  
        pm.popupMenu( parent = self.widgetName )
        if self.task=='asset':
            pm.menuItem(l='remove asset', c=self.removeCallback)
        elif self.task=='shot':
            pm.menuItem(l='shot manager', c=self.shotManagerCallback)
            pm.menuItem(l='remove shot', c=self.removeCallback)        
        else:
            pm.menuItem(l='assemble', c=self.assembleCallback)
            pm.menuItem(l='open', c=self.openCallback)        

class ComponentWidget(ItemWidget):
    def __init__(self, name, imgPath, label , parentWidget, color = (0,.2,.50)):
        super(ComponentWidget, self).__init__(name, imgPath, label , parentWidget, color)
    
    def removeComponentCallBack(self, *args):
        item = self.parentWidget.item
        projectName = self.parentWidget.projectName
        ns= self.name.split(':')[0]
        removeComponent (item, ns)
        pm.evalDeferred( 'pm.deleteUI("'+self.widgetName+'")')
        self.parentWidget.itemList.remove(self)
        
    def addToLayout(self):
        self.widgetName = pm.iconTextButton( self.name,  p= self.parentWidget.widgetName ,backgroundColor=self.color,  style='iconAndTextHorizontal', image=self.imgPath, label=self.label ,h=80, w=160, doubleClickCommand=self.dClickCallBack, command=self.clickCallBack , dragCallback = self.dragCallback )  
        pm.popupMenu( parent = self.widgetName )
        pm.menuItem(l='remove component', c= self.removeComponentCallBack)      

class ItemListWidget(object):
    def __init__(self): 
        global db
        self.parentWidget = None
        self.widgetName = None
               
        self.folderTreeWidget = None
        self.infoWidget=None 
        
        self.itemList = [] 
        self.selectedItem = None
        self.type = None
        self.task = None
        self.path = None        
        
        proj = db.projects.find_one()
        self.projectName=proj['projectName']                                             

    def createList(self,parentWidget):
        self.parentWidget = parentWidget
        a = pm.scrollLayout(p=self.parentWidget , childResizable=True, h=400)
        self.widgetName = pm.flowLayout(p=a, backgroundColor=(.17,.17,.17), columnSpacing=5, h=1000, wrap=True)
        pm.popupMenu( parent=self.widgetName )
        pm.menuItem(l='add item', c=self.addItemCallBack)  

    def refreshList(self, path=None, task=None, code=None, item=None):
        global db
        itemListProj = db.projects.find_one({'projectName':self.projectName})
        
        if item:
            self.path=item['path']
            self.task=item['task']
            self.type=item['type']
        else:
            self.path = path 
            self.task = task
            self.type = getTaskType(task)      
        
        collection = db.get_collection( itemListProj[self.type+'Collection'] )        
  
        if code:
            result = collection.find ({'path':self.path, 'code':code})    
        else:
            if self.task=='asset':
                result = collection.find ({'path':self.path, 'task':'model'})
            elif self.task =='shot':
                result = collection.find ({'path':self.path, 'task':'layout'})
            else:
                result = collection.find ({'path':self.path, 'task':task})
                
                    
        childs = pm.flowLayout(self.widgetName, q=True, ca = True)
        if childs:
            for i in childs:
                pm.deleteUI(i)               
        
        self.itemList=[]
        self.selectedItem = None  
        
        for item in result:
            itemName = templateName (item)           
            if not code and (task=='asset' or task=='shot') :
                templ=[x for x in itemListProj['assetNameTemplate'] if x!='$task']                        
                itemLabel= templateName (item, template=templ)
                createdColor = (0,.2,.50)
                notCreatedColor = (0,.2,.50)
            else:
                itemLabel = itemName
                notCreatedColor = (.2,.2,.2)
                createdColor = (1,.8,.20)

                                   
            status = item['status']
            if status=='notCreated':
                color = notCreatedColor
            elif status =='created':
                color = createdColor
                
            if self.type=='asset':    
                x = ItemWidget(itemName, u'D:/JOBS/PIPELINE/pipeExemple/scenes/icons/dino.jpg', itemLabel , self , color)
            elif self.type=='shot':  
                x = ItemWidget(itemName, u'D:/JOBS/PIPELINE/pipeExemple/scenes/icons/robot.jpg', itemLabel , self , color) 
                
            x.infoWidget= self.infoWidget

            if code:
                x.task = item['task']
                x.workVer = item['workVer']
                x.publishVer = item['publishVer']
            else:
                x.task = self.task
                x.workVer = 0
                x.publishVer = 0
                
            x.code = item['code']        
            self.itemList.append(x)
            x.addToLayout()
                          
    def addItemCallBack (self, *args):
        if not self.path:
            return pm.confirmDialog( title='error',ma='center', message='please choose a folder where to create the asset', button=['OK'], defaultButton='OK', dismissString='OK')     

        pm.layoutDialog(ui= lambda :self.createAssetPrompt())
        self.refreshList(path = self.path, task = self.task)

    def createAssetPrompt(self):
        global db
        proj = db.projects.find_one({'projectName':self.projectName})
        if self.type=='asset':
            code = "%04d" % proj['nextAsset']
        elif self.type=='shot':
            code = "%04d" % proj['nextShot']
            
        form = pm.setParent(q=True)
        f = pm.formLayout(form, e=True, width=150)
        row=pm.rowLayout(nc=2, adj=2)
        pm.picture( image='sphere.png', w=50, h=50 )
        col = pm.columnLayout(adjustableColumn=True)
        nameField  = pm.textFieldGrp('CrAsset_nameField', label='Name',cw=(1,70), text='', adj=2, cat=[(1,'left',5),(2,'left',5) ], editable=True )
        codeField  = pm.textFieldGrp('CrAsset_codeField', label='Code',cw=(1,70), text=code , adj=2, cat=[(1,'left',5),(2,'left',5) ], editable=True )
        workflow = pm.optionMenuGrp('CrAsset_workflowOpt', label='Workflow',cw=(1,70), cat=[(1,'left',5),(2,'left',5)] )
        proj = db.projects.find_one({'projectName':self.projectName})

        for key in proj['workflow']:      
            context = set([proj['workflow'][key][x]['type'] for x in proj['workflow'][key]])
            if self.type in context:
                pm.menuItem( label=key )
                
        b1 = pm.button(p=f, l='Cancel', c=self.abortCreateCallback )
        b2 = pm.button(p=f, l='OK', c=self.createAssetCallBack )
    
        spacer = 5
        top = 5
        edge = 5
        pm.formLayout(form, edit=True, attachForm=[(row, 'right', edge),(row, 'top', top), (row, 'left', edge),
                                                   (row, 'right', edge), (b1, 'right', edge), (b1, 'bottom', edge),
                                                   (b2, 'left', edge), (b2, 'bottom', edge)],
                                        attachNone=[],
                                        attachControl=[],
                                        attachPosition=[(b1, 'right', spacer, 90), (b2, 'left', spacer, 10)])
    
    def abortCreateCallback (self, *args):
        pm.layoutDialog( dismiss="Abort" )    

    def createAssetCallBack(self, *args):
        name = pm.textFieldGrp('CrAsset_nameField', q=True, tx=True)
        if not name:
            return pm.confirmDialog( title='error',ma='center', message='please choose a name for the asset', button=['OK'], defaultButton='OK', dismissString='OK') 
        workflow = pm.optionMenuGrp('CrAsset_workflowOpt', q=True, v=True) 
        code = pm.textFieldGrp('CrAsset_codeField', q=True, tx=True)
               
        itemDict = createItem(self.type, name, self.path, workflow, code)
        if itemDict=='codeExists':
            return pm.confirmDialog( title='error',ma='center', message='this code already exists', button=['OK'], defaultButton='OK', dismissString='OK') 
        pm.layoutDialog( dismiss='ok')

class componentListWidget(ItemListWidget):
    def __init__(self): 
        self.item=None
        super(componentListWidget, self).__init__()

    def dropCallback (self, dragControl, dropControl, messages, x, y, dragType  ):
        if messages[0]=='rig' or messages[0]=='uvs':
            addComponent(self.item, 'ref', messages[0], messages[1], 'reference')
            self.refreshList(item=self.item)
        else:
            pm.confirmDialog( title='error',ma='center', message='please choose rigs or uvs!', button=['OK'], defaultButton='OK', dismissString='OK')    
            
    def createList(self,parentWidget):
        self.parentWidget = parentWidget
        a = pm.scrollLayout(p=self.parentWidget , childResizable=True, h=400)
        self.widgetName = pm.flowLayout(p=a, backgroundColor=(.17,.17,.17), columnSpacing=5, h=1000, wrap=True,dropCallback=self.dropCallback )
        pm.popupMenu( parent=self.widgetName )
        pm.menuItem(l='add item', c=self.addItemCallBack)  
                                       
    def refreshList(self, path=None, task=None, code=None, item=None):
        global db
        if not item:
            print 'ERROR: No seach item!!'
            
        self.item = item
        itemListProj = db.projects.find_one({'projectName':self.projectName})
        type = 'shot'      
        collection = db.get_collection( itemListProj[type+'Collection'] )        
               
        childs = pm.flowLayout(self.widgetName, q=True, ca = True)
        if childs:
            for i in childs:
                pm.deleteUI(i)  
        
        self.itemList=[]
        self.selectedItem = None
        for ns, component in item['components'].iteritems():
            type = component['type']
            collection = db.get_collection( itemListProj[type+'Collection'] )    
            result = collection.find_one ({'task':component['task'], 'code':component['code']}) 
 
            if not result:
                print 'component %s %s missing!' % (component['task'], component['code'])
                continue
                
            itemName = ns+':'+getTaskShort(result['task'])+result['code']+'_'+result['name'] 

            if result['task']=='rig':
                createdColor = (0,.5,.20)
            elif result['task']=='uvs':
                createdColor = (.5,.5,.20)
                
            notCreatedColor = (.2,.2,.2)    
                
            status = result['status']
            if status=='notCreated':
                color = notCreatedColor
            elif status =='created':
                color = createdColor             
                    
            x = ComponentWidget(itemName, 'cube.png', itemName , self , color)
            self.itemList.append(x)
            x.task=result['task']
            x.code=result['code']
            x.addToLayout()
                          
    def addItemCallBack (self, *args):
        pm.layoutDialog(ui= lambda :self.createAssetPrompt())
        self.refreshList(item=self.item)

    def createAssetPrompt(self):
        form = pm.setParent(q=True)
        f = pm.formLayout(form, e=True, width=150)
        
        col2 = pm.columnLayout(p=f, adjustableColumn=True) 
        nsField = pm.textFieldGrp ('nsFieldPrompt', l='Name Space', tx='ref' )
        refModeField = pm.optionMenuGrp (l='Assemble Mode' )
        pm.menuItem (l='reference')
        pm.menuItem (l='cache')
        pm.menuItem (l='import') 
        pm.menuItem (l='copy')   
        pane = pm.paneLayout(p=col2, configuration='top3', ps= [(1,20,80),(2,80,80), (3,100,20)])
        folderTreeWidget=FolderTreeWidget()
        folderTreeWidget.createFolderTree(pane)
        folderTreeWidget.projectName = self.projectName
        folderTreeWidget.type='asset'
        folderTreeWidget.getFolderTree()
                
        itemListWidget = ItemListWidget()
        itemListWidget.projectName = self.projectName
        itemListWidget.createList(pane)        
        itemListWidget.refreshList(path=[],task='rig')
                
        infoWidget = InfoWidget()
        infoWidget.createInfo(pane)
                
                
        folderTreeWidget.itemListWidget=itemListWidget
        folderTreeWidget.itemListWidget.type='asset'
        folderTreeWidget.itemListWidget.task='rig'
        itemListWidget.infoWidget = infoWidget   
                
        b1 = pm.button(p=f, l='Cancel', c='pm.layoutDialog( dismiss="Abort" )' )
        b2 = pm.button(p=f, l='OK', c=lambda x: self.createAssetCallBack (itemListWidget.selectedItem ) )
    
        spacer = 5
        top = 5
        edge = 5
        pm.formLayout(form, edit=True, attachForm=[(col2, 'right', edge),(col2, 'top', top), (col2, 'left', edge),
                                                   (b1, 'right', edge), (b1, 'bottom', edge),
                                                   (b2, 'left', edge), (b2, 'bottom', edge)],
                                        attachNone=[],
                                        attachControl=[],
                                        attachPosition=[(b1, 'right', spacer, 90), (b2, 'left', spacer, 10)])
        
    def createAssetCallBack(self, component, *args):
        if component:
            ns = pm.textFieldGrp ('nsFieldPrompt', q=True, tx=True)
            addComponent (self.item, ns, component.task, component.code, 'reference')
            pm.layoutDialog( dismiss='ok')
        
class  FolderTreeWidget():
    def __init__(self):
        global db
        self.widgetName=None        
        self.parentWidget = None
        self.type='asset'
                
        self.itemListWidget=None
        
        proj = db.projects.find_one()
        self.projectName=proj['projectName']
                                                      
    def createFolderTree(self, parent):
        self.parentWidget = parent
        self.widgetName = pm.treeView(p=self.parentWidget,  numberOfButtons = 0, abr = False )        
        pm.treeView( self.widgetName , e=True, selectionChangedCommand = self.selChangedCallBack)
        pm.popupMenu( parent=self.widgetName )
        pm.menuItem(l='add folder', c=self.addFolderCallBack)
        pm.menuItem(l='remove folder', c=self.removeFolderCallBack)
        if self.projectName:
            self.getFolderTree() 
        
    def addFolderCallBack(self,*args):
        print 'add folder'    
        sel= pm.treeView(self.widgetName, q=True, si = True)
        if sel:
            pm.treeView(self.widgetName, e=True, addItem = ('new Folder', sel[0]))
        else:
            pm.treeView(self.widgetName, e=True, addItem = ('new Folder', ''))
                   
    def removeFolderCallBack(self,*args):
        print 'remove folder'
        sel= pm.treeView(self.widgetName, q=True, si = True)
        if sel:
            pm.treeView(self.widgetName, e=True, removeItem = sel[0])
        else:
            print 'select a folder to remove!!' 
            
    def selChangedCallBack(self,*args):
        sel = pm.treeView(self.widgetName , q=True, si = True)    
        if sel:
            if self.itemListWidget:       
                self.itemListWidget.path = self.getSelectedPath()
                self.itemListWidget.type = self.type             
                self.itemListWidget.refreshList(path = self.itemListWidget.path, task = self.itemListWidget.task, code=None)
                
    def getSelectedPath(self):
        sel = pm.treeView( self.widgetName, q=True, si = True)
        if sel:
            child = sel[0]
            parent = 'start'
            path=[child]
            while parent:
                parent =  pm.treeView(self.widgetName, q=True, ip = child)               
                child=parent
                if child:
                    path.append(child)
        return list(reversed(path))

    def putFolderTree(self):
        allItems = pm.treeView( self.widgetName, q=True, children = True)
        folderTreeDict={}
        for item in allItems:
            par= pm.treeView( self.widgetName, q=True, itemParent = item)
            folderTreeDict[item]=par
        return folderTreeDict
    
    def getFolderTree(self):
        global db
        proj = db.projects.find_one({'projectName': self.projectName})
        folderTreeDict= proj[self.type+'Folders'] 
                       
        allKeys = folderTreeDict.keys()        
        parentList=[x for x in folderTreeDict if folderTreeDict[x]==''] 
        parentList.sort()
        pm.treeView( self.widgetName, e=True, ra = True)
        for item in parentList:
            pm.treeView( self.widgetName, e=True, addItem = (item, ''))      
        
        while allKeys:
            allKeys=[x for x in allKeys if not x in parentList]
            parentList = [x for x in folderTreeDict if folderTreeDict[x] in parentList ] 
            parentList.sort()
            for item in parentList:
                pm.treeView( self.widgetName, e=True, addItem = (item, folderTreeDict[item]))
                
                

         
class InfoWidget():
    def __init__(self):
        self.widgetName=None
        self.parentWidget = None
        
        self.statusField = None
        self.nameInfoField = None
        self.taskField = None
        self.codeField = None
        self.workVerField = None
        self.publishVerField = None
        self.task = False
        self.col = None
            
    def createInfo(self,parent):
        self.parentWidget = parent        
        self.widgetName =pm.rowLayout(p=self.parentWidget ,nc=2, adj=2)
        pm.picture(p=self.widgetName , image=u'D:\JOBS\PIPELINE\pipeExemple\scenes\icons\dragon.png', w=150, h=150 )
        self.col = pm.columnLayout('col', adjustableColumn=True)
        self.statusField = pm.textFieldGrp('statusInfo', label='Status', cw=(1,100), text='', adj=2, cat=(1,'left',20) , editable=False)
        self.nameInfoField  = pm.textFieldGrp('nameInfo', label='Name',cw=(1,100), text='', adj=2, cat=(1,'left',20), editable=False )
        self.codeField = pm.textFieldGrp('codeInfo', label='Code',cw=(1,100), text='', adj=2, cat=(1,'left',20), editable=False )
        self.taskField = pm.textFieldGrp( 'taskinfo', label='Task',cw=(1,100), text='', adj=2, cat=(1,'left',20), editable=False )    
        self.workVerField = pm.intFieldGrp('WorkVersion',  label='Work Version',w=60,cw=(1,100), value1= 1 , adj=2, cat=(1,'left',20), enable=False)
        self.publishVerField = pm.intFieldGrp('PublishVersion', label='Publish Version',w=60,cw=(1,100), value1= 1 , adj=2, cat=(1,'left',20), enable=False)

    def putItemInfo (self, item):
        pm.textFieldGrp(self.nameInfoField, e=True, tx=item['name'])
        pm.textFieldGrp(self.codeField, e=True, tx=item['code'])          
        pm.textFieldGrp(self.taskField, e=True, tx=item['task'])      
        pm.intFieldGrp(self.workVerField, e=True, value1=item['workVer'])      
        pm.intFieldGrp(self.publishVerField , e=True, value1=item['publishVer'])  

    def putInfo (self, itemWidget):
        name =  itemWidget.name.split('_')[1]
        short = itemWidget.name[0:2]
        code = itemWidget.name.split('_')[0][3:] ### hard coding!!
        pm.textFieldGrp(self.nameInfoField, e=True, tx=name)
        pm.textFieldGrp(self.codeField, e=True, tx=code)          
        pm.textFieldGrp(self.taskField, e=True, tx=itemWidget.task)      
        pm.intFieldGrp(self.workVerField, e=True, value1=itemWidget.workVer)      
        pm.intFieldGrp(self.publishVerField , e=True, value1=itemWidget.publishVer)  
            
            

class itemBrowser():
    def __init__(self):
        self.createBrowser()            
            
    def createBrowser(self):
        win=pm.window(w=800, h=600)
        col2 = pm.columnLayout(adjustableColumn=True)
        allowedAreas = ['right', 'left']
        pm.dockControl(l='SHOT INFO', w=600, area='left', content=win, allowedArea=allowedAreas)
        
        self.projectSelectWidget = ProjectSelectWidget()
        self.projectSelectWidget.createProjectSelect(col2)
        
        self.typeOpt = pm.optionMenuGrp (l='Item Type', changeCommand = self.changeTypeCallback )
        types = ['asset', 'shot', 'model', 'uvs', 'texture', 'blendShape', 'rig', 'layout', 'animation', 'shotFinalizing', 'lightining', 'render']
        for type in types:
            pm.menuItem (l=type)

        pane = pm.paneLayout(p=col2, configuration='top3', ps=[(1,20,80),(2,80,80), (3,100,20)])

        self.folderTreeWidget = FolderTreeWidget()
        self.folderTreeWidget.createFolderTree(pane)
        self.folderTreeWidget.type='asset'
        self.folderTreeWidget.getFolderTree()
        
        self.itemListWidget = ItemListWidget()
        self.itemListWidget.createList(pane)        
        self.itemListWidget.refreshList(path=[],task='asset')
        
        self.infoWidget = InfoWidget()
        self.infoWidget.createInfo(pane)
                
        self.folderTreeWidget.itemListWidget=self.itemListWidget
        self.folderTreeWidget.itemListWidget.type='asset'
        self.folderTreeWidget.itemListWidget.task='asset'
        self.projectSelectWidget.folderTreeWidget = self.folderTreeWidget
        self.projectSelectWidget.itemListWidget = self.itemListWidget
        self.itemListWidget.infoWidget = self.infoWidget

        pm.showWindow()

    def changeTypeCallback (self,newTaskToSeach, *args):
        projName = self.projectSelectWidget.projectName
        
        type = getTaskType(newTaskToSeach)
        
        self.itemListWidget.type=type
        
        self.folderTreeWidget.type=type
        self.folderTreeWidget.getFolderTree()
        
        self.itemListWidget.task=newTaskToSeach        
        self.itemListWidget.refreshList(path =self.itemListWidget.path,task=self.itemListWidget.task)
                
class ShotManager():
    def __init__(self, item):
        self.item=item
        self.infoWidget =None
        self.compListWidget = None
        self.projectName= None           
            
    def createShotManager(self):        
        win=pm.window(title='SHOT MANAGER', w=800, h=600)
        pane = pm.paneLayout( configuration='horizontal2')
        self.infoWidget = InfoWidget()
        self.infoWidget.createInfo(pane)
        self.infoWidget.putItemInfo (self.item)
        self.compListWidget = componentListWidget()
        self.compListWidget.projectName = self.projectName
        self.compListWidget.createList(pane)        
        
        pm.showWindow()             
        self.compListWidget.refreshList(item = self.item)

class ProjectSelectWidget():
    def __init__(self):
        self.widgetName=None
        self.parentWidget = None
        self.projectName = None
        self.folderTreeWidget=None
        self.itemListWidget=None

    def makePopup(self):
        global db
        global currentProject

        self.projPopUp = pm.popupMenu( parent=self.widgetName )
        pm.menuItem( l='new project', c=self.newProjectCallback)     
        allProjects = db.projects.find()

        for proj in allProjects:
            if not self.projectName:
                self.projectName = proj['projectName']
                currentProject = self.projectName
                self.changeProjectCallBack(self.projectName)   

            pm.menuItem( l=proj['projectName'], c = lambda x, y=proj['projectName'] : self.changeProjectCallBack(y))
           
    def createProjectSelect(self,parent):
        self.parentWidget = parent        
        self.widgetName  = pm.textFieldButtonGrp ('projectSel', p = self.parentWidget, label='ProjectName', text='projeto', cat=(1,'left',20) ,adj=2,bl='...', bc=self.projectSettingsCallback )
        pm.separator( height=40, style='in' )
        self.makePopup()
     
    def newProjectCallback(self, *args):
        proj = ProjectSettingsWidget()
        proj.createProjectSettingsWidget()
        proj.new = True
        proj.parentWidget = self
        pm.textFieldGrp (proj.projNameTxt, e=True, editable=True) 
        pm.textFieldGrp (proj.prefixTxt, e=True, editable=True)   
        
    def projectSettingsCallback (self,*args):
        proj = ProjectSettingsWidget(self.projectName)
        proj.createProjectSettingsWidget()
              
    def changeProjectCallBack(self,projName):
        global currentProject

        pm.textFieldButtonGrp(self.widgetName, e=True, text=projName) 

        if self.projectName != projName :  
            self.projectName = projName
            currentProject = self.projectName

            if self.folderTreeWidget:
                self.folderTreeWidget.projectName= self.projectName
                self.folderTreeWidget.getFolderTree()

            if self.itemListWidget:
                self.itemListWidget.projectName = self.projectName
                self.itemListWidget.refreshList (path=[],task = self.itemListWidget.task)
                
                
    def getProject(self):
        global db
        shortName= pm.layout(self.widgetName, q=True, ca=True)[1]
        fullName= pm.layout(shortName, q=True,fpn=True)
        projName=pm.textField(fullName, q=True, text=True)
        proj=db.projects.find_one({'projectName':projName})
        return proj
                
class ProjectSettingsWidget():
    def __init__(self, projectName=None):
        self.parentWidget=None
        self.projectName = projectName
        self.projDict = None
        self.new = False
                
    def okCallback(self, *args):
        global db       
        self.putProjectSettings()       
        projName = self.projDict['projectName']

        if self.new:
            if not projName:
                print 'Please choose a name for the project!!'
                return  

            existName = db.projects.find_one({'projectName':projName})

            if existName:
                print 'This Name exists. Please choose another name' 
                return 

            print 'create project'
            print self.projDict       
            addProject (db,**self.projDict)
            pm.deleteUI (self.parentWidget.projPopUp)
            self.parentWidget.makePopup()
            self.parentWidget.changeProjectCallBack(projName)

        else:
            print 'edit project'
            db.projects.find_one_and_update({'projectName':projName},{'$set':self.projDict} )    
                         
        pm.deleteUI(self.win)
        
    def cancelCallback(self, *args):
        pm.deleteUI(self.win)


    def addFolderCallBack(self,widget,*args):
        print 'add folder'    
        sel= pm.treeView(widget, q=True, si = True)
        if sel:
            pm.treeView(widget, e=True, addItem = ('new Folder', sel[0]))
        else:
            pm.treeView(widget, e=True, addItem = ('new Folder', ''))
                   
    def removeFolderCallBack(self,widget, *args):
        print 'remove folder'
        sel= pm.treeView(widget, q=True, si = True)
        if sel:
            pm.treeView(widget, e=True, removeItem = sel[0])
        else:
            print 'select a folder to remove!!' 
                  
    def createProjectSettingsWidget(self): 
        global db
        if not self.projectName:
            self.projDict = getDefaultDict()
        else:
            self.projDict = db.projects.find_one({'projectName':self.projectName})
                                                   
        self.win=pm.window(w=800, h=600)
        col = pm.columnLayout(adjustableColumn=True,columnAlign='left', )
        self.projNameTxt = pm.textFieldGrp( label='ProjectName', text=self.projDict ['projectName'], cat=(1,'left',20),adj=2, editable = False )
        self.prefixTxt = pm.textFieldGrp( label='Prefix', text=self.projDict ['prefix'], cat=(1,'left',20),adj=2, editable = False )
        self.statusOpt = pm.optionMenuGrp( l='Status',cat=(1,'left',20) )
        pm.menuItem( label='inative' )
        pm.menuItem( label='active' )
        pm.menuItem( label='current' )
        pm.optionMenuGrp( self.statusOpt, e=True,v=self.projDict ['status'] )
        self.workLocTxt = pm.textFieldButtonGrp( label='Work Location', text=self.projDict ['workLocation'] , buttonLabel='...' , adj=2, cat=(1,'left',20))
        self.publishLocTxt = pm.textFieldButtonGrp( label='Publish Location', text=self.projDict ['publishLocation'], buttonLabel='...', adj=2, cat=(1,'left',20) )
        self.cacheLocTxt = pm.textFieldButtonGrp( label='Cache Location', text=self.projDict ['cacheLocation'], buttonLabel='...', adj=2, cat=(1,'left',20) )
        self.assetCollTxt = pm.textFieldGrp( label='Asset Collection', text=self.projDict ['assetCollection'], adj=2, cat=(1,'left',20),editable=False )
        self.shotCollTxt = pm.textFieldGrp( label='Shot Collection', text=self.projDict ['shotCollection'], adj=2, cat=(1,'left',20),editable=False )
        self.nameTemplTxt = pm.textFieldGrp( label='Asset Name Template', text=','.join(self.projDict ['assetNameTemplate']), adj=2, cat=(1,'left',20) )
        self.cacheTemplTxt = pm.textFieldGrp( label='Cache Name Template', text=','.join(self.projDict ['cacheNameTemplate']), adj=2, cat=(1,'left',20) )
        self.rendererOpt  = pm.optionMenuGrp(label='Renderer',cat=(1,'left',20))
        pm.menuItem( label='vray' )
        pm.menuItem( label='arnold' )
        pm.optionMenuGrp( self.rendererOpt, e=True, v= self.projDict ['renderer'] )
        self.resolutionOpt = pm.optionMenuGrp( l='Resolution',cat=(1,'left',20) )
        pm.menuItem( label='1920x1080' )
        pm.menuItem( label='2048x1780' )
        pm.optionMenuGrp( self.resolutionOpt, e=True,v= '%sx%s' % (self.projDict ['resolution'][0],self.projDict ['resolution'][1])  )
        pm.text (p=col,l='FOLDERS')
        pane = pm.paneLayout(p=col,cn='vertical2', h=150)
        self.assetTreeView = pm.treeView( parent = pane, numberOfButtons = 0, abr = False  )
        for folder,parent in self.projDict['assetFolders'].iteritems():
            pm.treeView( self.assetTreeView, e=True, addItem = (folder, parent))
        pm.popupMenu( parent=self.assetTreeView)
        pm.menuItem(l='add folder', c=lambda x: self.addFolderCallBack(self.assetTreeView))
        pm.menuItem(l='remove folder', c=lambda x: self.removeFolderCallBack(self.assetTreeView))
        
        self.shotTreeView = pm.treeView( parent = pane, numberOfButtons = 0, abr = False )
        for folder,parent in self.projDict['shotFolders'].iteritems():
            pm.treeView( self.shotTreeView , e=True, addItem = (folder, parent))
        pm.popupMenu( parent=self.shotTreeView)
        pm.menuItem(l='add folder', c=lambda x: self.addFolderCallBack(self.shotTreeView) )
        pm.menuItem(l='remove folder', c=lambda x: self.removeFolderCallBack(self.shotTreeView) )

        pm.text (p=col,l='WORKFLOWS')
        pane = pm.paneLayout(p=col,cn='vertical2', h=100)
        
        self.workflowScrll= pm.textScrollList( parent = pane )
        for workflow in self.projDict['workflow']:
            pm.textScrollList( self.workflowScrll, e=True, append = '     '+workflow)
        
        pm.rowLayout (p=col, nc=3, adj=1)
        pm.text (l='')
        pm.button (l='OK', w=50,h=50, c= self.okCallback )
        pm.button (l='Cancel', w=50,h=50, c =self.cancelCallback)
        
        pm.showWindow()

    def putProjectSettings(self):                                         
        self.projDict ['projectName'] = pm.textFieldGrp(self.projNameTxt,  q=True, text=True )
        self.projDict ['prefix'] = pm.textFieldGrp(self.prefixTxt,  q=True, text=True )
        self.projDict ['status'] = pm.optionMenuGrp(self.statusOpt,  q=True, v=True )
        self.projDict ['workLocation']= pm.textFieldButtonGrp( self.workLocTxt , q=True, text=True)
        self.projDict ['publishLocation']  = pm.textFieldButtonGrp(self.publishLocTxt, q=True, text=True)
        self.projDict ['cacheLocation']  = pm.textFieldButtonGrp(self.cacheLocTxt ,  q=True, text=True)
        self.projDict ['assetCollection']  = self.projDict ['projectName']+'_asset'
        self.projDict ['shotCollection'] = self.projDict ['projectName']+'_shot'
        nameTemplateString = pm.textFieldGrp(self.nameTemplTxt , q=True,  text=True )
        self.projDict ['assetNameTemplate'] = nameTemplateString.split(',')
        cacheTemplateString = pm.textFieldGrp(self.cacheTemplTxt , q=True,  text=True )
        self.projDict ['cacheNameTemplate'] = cacheTemplateString.split(',')
        self.projDict ['renderer'] = pm.optionMenuGrp(self.rendererOpt, q=True, v=True)
         
        res = pm.optionMenuGrp(self.resolutionOpt , q=True, v=True)
        self.projDict ['resolution'] = [int (res.split('x')[0]), int (res.split('x')[1])]
        allItems = pm.treeView( self.assetTreeView, q=True, children = True)
        folderTreeDict={}
        
        if allItems:
            for item in allItems:
                par= pm.treeView( self.assetTreeView, q=True, itemParent = item)
                folderTreeDict[item]=par
        self.projDict['assetFolders'] = folderTreeDict

        allItems = pm.treeView( self.shotTreeView, q=True, children = True)
        folderTreeDict={}
        if allItems:
            for item in allItems:
                par= pm.treeView( self.shotTreeView, q=True, itemParent = item)
                folderTreeDict[item]=par            
        self.projDict['shotFolders'] = folderTreeDict
        