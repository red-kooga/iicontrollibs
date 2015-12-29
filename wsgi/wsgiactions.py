def application(environ, start_response):

    import cgi
    import json

    import os, sys, inspect

    # Set top folder to allow import of modules

    top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
    if top_folder not in sys.path:
        sys.path.insert(0,top_folder)

    import cupid.pilib as pilib
    import cupid.controllib as controllib

    post_env = environ.copy()
    post_env['QUERY_STRING'] = ''
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    formname=post.getvalue('name')
    output = {}
    output['message'] = 'Output Message: '
    d = {}
    for k in post.keys():
        d[k] = post.getvalue(k)

    status = '200 OK'
    wsgiauth = False
    authverified = False

    if wsgiauth:
        # Verfiy that session login information is legit: hashed password, with salt and username, match
        # hash stored in database.
        import hashlib
        from pilib import salt

        try:
            userdata = pilib.datarowtodict(pilib.usersdatabase, 'users', pilib.sqlitequery(pilib.usersdatabase, "select * from users where name='" + d['sessionuser'] + "'")[0])
        except:
            output['message'] += 'error in user sqlite query. '
            # unsuccessful authentication

        # Get session hpass to verify credentials
        hashedpassword = d['sessionhpass']
        hname = hashlib.new('sha1')
        hname.update(d['sessionuser'])
        hashedname = hname.hexdigest()
        hentry = hashlib.new('md5')
        hentry.update(hashedname + salt + hashedpassword)
        hashedentry = hentry.hexdigest()
        if hashedentry == userdata['password']:
            # successful auth
            output['message'] += 'Password verified. '
            authverified = True
    else:
        output['message'] += 'WSGI authorization not enabled. '

    if authverified or not wsgiauth:
        # Perform requested actions
        if 'action' in d:
            action = d['action']
            output['message'] += 'Found action. '
            if action == 'runquery':
                output['message'] += 'Query keyword found. '
                if 'query' in d:  # Take plain single query
                    result = pilib.sqlitequery(d['database'], d['query'])
                    output['response'] = result
                    output['message'] += 'Query executed. '
                elif 'queryarray[]' in d:  # Take query array, won't find
                    result = []
                    queryarray = d['queryarray[]']
                    for query in queryarray:
                        result.append(pilib.sqlitequery(d['database'], query))
                    output['response'] = result
                    output['message'] += 'Query array executed. '
            elif action == 'testmodule':
                output['message'] += 'Testing module: '
                if 'modulename' in d:
                    import cupid.cupidunittests
                    output['message'] += d['modulename']
                    output['data'] = cupid.cupidunittests.testmodule(d['modulename'])
                else:
                    output['message'] += 'Modulename not found. '
            elif action == 'testfunction':
                output['message'] += 'Testing function: '
                if 'testname' in d:
                    import cupid.cupidunittests
                    output['message'] += d['testname']
                    # output['data'] = cupid.tests.testfunction(d['testname'])
                    output['data'] = cupid.cupidunittests.testfunction(d['testname'])
                    # output['data'] = str(cupid.tests.testfunction('systemstatus'))
                else:
                    output['message'] += 'Testname not found. '
            elif action == 'dump':
                if 'database' in d and 'tablelist' in d and 'outputfile' in d:
                    pilib.sqlitedatadump(d['database'],d['tablelist'],d['outputfile'])
                    output['message'] = 'data dumped'
                elif 'database' in d and 'tablename' in d and 'outputfile' in d:
                    pilib.sqlitedatadump(d['database'],[d['tablename']],d['outputfile'])
                    output['message'] = 'data dumped'
                else:
                    data = 'keys not present for dump'
            elif action in ['userdelete', 'useradd', 'usermodify']:

                # Ensure that we are authorized for this action
                if userdata['authlevel'] >= 4:
                    output['message'] += 'User selected has sufficient authorizations. '
                    if action == 'userdelete':
                        try:
                            pilib.sqlitequery(pilib.usersdatabase, "delete from users where name='" + d['usertodelete'] + "'")
                        except:
                            output['message'] += 'Error in delete query. '
                        else:
                            output['message'] += 'Successful delete query. '
                    elif action == 'usermodify':
                        if 'usertomodify' in d:
                            querylist=[]
                            if 'newpass' in d:
                                # Get session hpass to verify credentials
                                hashedpassword = d['newpass']
                                hname = hashlib.new('sha1')
                                hname.update(d['usertomodify'])
                                hashedname = hname.hexdigest()
                                hentry = hashlib.new('md5')
                                hentry.update(hashedname + salt + hashedpassword)
                                hashedentry = hentry.hexdigest()
                                querylist.append('update users set password=' + hashedentry + " where name='" + d['usertomodify'] + "'")
                            if 'newemail' in d:
                                querylist.append("update users set email='" + d['newemail'] + "' where name='" + d['usertomodify'] + "'")
                            if 'newauthlevel' in d:
                                querylist.append("update users set authlevel='" + d['newauthlevel'] + "' where name='" + d['usertomodify'] + "'")

                            try:
                                pilib.sqlitemultquery(pilib.usersdatabase, querylist)
                            except:
                                output['message'] += 'Error in modify/add query: ' + ",".join(querylist)
                            else:
                                output['message'] += 'Successful modify/add query. ' + ",".join(querylist)
                        else:
                            output['message'] += 'Need usertomodify in query. '
                    elif action == 'useradd':
                        try:
                            username = d['newusername']
                        except:
                            username = 'newuser'
                        try:
                            newemail = d['newemail']
                        except:
                            newemail = 'fakeemail@domain.com'
                        try:
                            newauthlevel = d['newauthlevel']
                        except:
                            newauthlevel = 0
                            query = "insert into users values(NULL,'" + username + "','','" + newemail + "',''," + str(newauthlevel) + ")"
                        try:
                            pilib.sqlitequery(pilib.usersdatabase, query)
                        except:
                            output['message'] += "Error in useradd sqlite query: " + query + ' . '
                        else:
                            output['message'] += "Successful query: " + query + ' . '
                    else:
                        output['message'] += 'Unable to verify password. '
                else:
                    output['message'] = 'insufficient authorization level for current user. '
            elif action == 'getfiletext':
                try:
                    filepath = d['filepath']
                    if 'numlines' in d:
                        numlines = int(d['numlines'])
                    else:
                        numlines = 9999
                    output['message'] += 'Using numlines: ' + str(numlines) + ' for read action. '
                    if 'startposition' in d:
                        startposition = d['startposition']
                    else:
                        startposition = 'end'
                    output['message'] += 'Reading from position ' + startposition + '. '
                except KeyError:
                    output['message'] += 'Sufficient keys for action getfile text do not exist. '
                except:
                    output['message'] += 'Uncaught error in getfiletext. '
                else:
                    try:
                        file = open(filepath)
                        lines = file.readlines()
                    except:
                        output['message'] += 'Error reading file in getfiletext action. '
                    else:
                        output['data'] = []
                        if startposition == 'end':
                            try:
                                output['data'] = pilib.tail(file, numlines)[0]
                            except:
                                output['message'] += 'Error in tail read. '
                        else:
                            linecount = 0
                            for line in lines:
                                linecount += 1
                                if linecount > numlines:
                                    break
                                else:
                                    output['data'].append(line)
            elif action == 'getmbtcpdata':
                try:
                    clientIP = d['clientIP']
                    register = d['register']
                    length = d['length']
                except KeyError:
                    output['message'] += 'Sufficient keys do not exist for the command. Requires clientIP, register, and length. '
                else:
                    from cupid.netfun import readMBcodedaddresses
                    # try:
                    output['response'] = readMBcodedaddresses(clientIP, int(register), int(length))
            elif action == 'queuemessage':
                output['message'] += 'Queue message. '
                if 'message' in d:
                    try:
                        pilib.sqliteinsertsingle(pilib.motesdatabase, 'queuedmessages', [pilib.gettimestring(), d['message']])
                    except Exception, e:
                        output['message'] += 'Error in queue insert query: ' + str(e)
                    else:
                        output['message'] += 'Message insert successful'
                else:
                    output['message'] += 'No message present. '
            elif action == 'setsystemflag' and 'systemflag' in d:
                database = pilib.systemdatadatabase
                pilib.setsinglevalue(database, 'systemflags', 'value', 1, "name=\'" + d['systemflag'] + "'")
            elif action == 'rundaemon':
                from cupiddaemon import rundaemon
                rundaemon()

            elif action == 'setvalue':
                pilib.log(pilib.controllog, "Setting value in wsgi", 1, 1)
                # we use the auxiliary 'setsinglecontrolvalue' to add additional actions to update
                if all(k in d for k in ('database', 'table', 'valuename', 'value')):
                    output['message'] += 'Carrying out setvalue. '
                    if 'condition' in d:
                        pilib.setsinglecontrolvalue(d['database'], d['table'], d['valuename'], d['value'], d['condition'])
                    elif 'index' in d:
                        condition = 'rowid= ' + d['index']
                        pilib.setsinglecontrolvalue(d['database'], d['table'], d['valuename'], d['value'], condition)
                    else:
                        pilib.setsinglecontrolvalue(d['database'], d['table'], d['valuename'], d['value'])
                else:
                    output['message'] += 'Insufficient data for setvalue '
            elif action == 'updateioinfo':
                if all(k in d for k in ['database', 'ioid', 'value']):
                    query = pilib.makesqliteinsert('ioinfo', [d['ioid'], d['value']], ['id', 'name'])
                    try:
                        pilib.sqliteinsertsingle(pilib.controldatabase, 'ioinfo', [d['ioid'], d['value']], ['id', 'name'])
                    except:
                        output['message'] += 'Error in updateioinfo query execution: ' + query +'. '
                        output['message'] += 'ioid: ' + d['ioid'] + ' . '
                    else:
                        output['message'] += 'Executed updateioinfo query. '
                else:
                    output['message'] += 'Insufficient data for updateioinfo query ! '

            # These are all very specific actions that could be rolled up or built into classes
            elif action == 'spchange' and 'database' in d:
                output['message'] += 'Spchanged. '
                if 'subaction' in d:
                    if d['subaction'] == 'incup':
                        controllib.incsetpoint(d['database'], d['channelname'])
                        output['message'] += 'incup. '
                    if d['subaction'] == 'incdown':
                        controllib.decsetpoint(d['database'], d['channelname'])
                        output['message'] += 'incdown. '
                    if d['subaction'] == 'setvalue':
                        controllib.setsetpoint(d['database'], d['channelname'], d['value'])
                        output['message'] += 'Setvalue: ' + d['database'] + ' ' + d['channelname'] + ' ' + d['value']
                else:
                    output['message'] += 'subaction not found. '
            elif action == 'togglemode' and 'database' in d:
                controllib.togglemode(d['database'], d['channelname'])
            elif action == 'setmode' and 'database' in d:
                controllib.setmode(d['database'], d['channelname'], d['mode'])
            elif action == 'setrecipe':
                controllib.setrecipe(d['database'], d['channelname'], d['recipe'])
            elif action == 'setcontrolinput':
                controllib.setcontrolinput(d['database'], d['channelname'], d['controlinput'])
            elif action == 'setchannelenabled':
                controllib.setchannelenabled(d['database'], d['channelname'], d['newstatus'])
            elif action == 'setchanneloutputsenabled':
                controllib.setchanneloutputsenabled(d['database'], d['channelname'], d['newstatus'])
            elif action == 'manualactionchange' and 'database' in d and 'channelname' in d and 'subaction' in d:
                curchanmode = pilib.controllib.getmode(d['database'], d['channelname'])
                if curchanmode == 'manual':
                    if d['subaction'] == 'poson':
                        controllib.setaction(d['database'], d['channelname'], '100.0')
                    elif d['subaction'] == 'negon':
                        controllib.setaction(d['database'], d['channelname'], '-100.0')
                    else:
                        controllib.setaction(d['database'], d['channelname'], '0.0')
            elif action == 'setposoutput' and 'database' in d and 'channelname' in d and 'outputname' in d:
                controllib.setposout(d['database'], d['channelname'], d['outputname'])
            elif action == 'setnegoutput' and 'database' in d and 'channelname' in d:
                controllib.setnegout(d['database'], d['channelname'], d['outputname'])
            elif action == 'actiondown' and 'database' in d and 'channelname' in d:
                curchanmode = controllib.getmode(d['database'], d['channelname'])
                if curchanmode == "manual":
                    curaction = int(controllib.getaction(d['database'], d['channelname']))
                    if curaction == 100:
                        nextvalue = 0
                    elif curaction == 0:
                        nextvalue = -100
                    elif curaction == -100:
                        nextvalue = -100
                    else:
                        nextvalue = 0
                    controllib.setaction(d['database'], d['channelname'], d['nextvalue'])
            elif action == 'actionup' and 'database' in d and 'channelname' in d:
                curchanmode = controllib.getmode(d['database'], d['channelname'])
                if curchanmode == "manual":
                    curaction = int(controllib.getaction(d['database'], d['channelname']))
                    if curaction == 100:
                        nextvalue = 100
                    elif curaction == 0:
                        nextvalue = 100
                    elif curaction == -100:
                        nextvalue = 0
                    else:
                        nextvalue = 0
                    controllib.setaction(d['database'], d['channelname'], nextvalue)
            elif action == 'deletechannelbyname' and 'database' in d and 'channelname' in d:
                pilib.sqlitequery(d['database'], 'delete channelname from channels where name=\"' + d['channelname'] + '\"')

            else:
                output['message'] += 'Action keyword present(' + action + '), but not handled. '

        else:
            output['message'] += 'action keyword not present. '
    else:
        output['message'] += 'Authentication unsuccessful'

    foutput = json.dumps(output, indent=1)

    response_headers = [('Content-type', 'application/json')]
    start_response(status, response_headers)

    return [foutput]

