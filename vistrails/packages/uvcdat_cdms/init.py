import ast
import cdms2
import cdutil
import genutil
import os
try:
    import cPickle as pickle
except:
    import pickle
import string
import vcs
import vtk

from vistrails.core import debug
from vistrails.core.modules.module_registry import get_module_registry
from vistrails.core.modules.vistrails_module import Module, ModuleError, \
    NotCacheable
from vistrails.packages.spreadsheet.basic_widgets import SpreadsheetCell
from vistrails.packages.spreadsheet.spreadsheet_controller import \
    spreadsheetController
from vistrails.packages.spreadsheet.spreadsheet_cell import QCellWidget
from vistrails.packages.uvcdat_cdms.vtk_classes import QVTKWidget


def unexpand_home_path(fullpath):
    """Replaces home path with ~ in the given filename, if it lies under it.

    >>> unexpand_home_path('/home/user/some/path')
    '~/some/path'
    >>> unexpand_home_path('/usr/local/path')
    '/usr/local/path'
    """
    if not fullpath or not os.path.isabs(fullpath):
        return fullpath
    homepath = os.path.expanduser('~') + '/'
    if fullpath.startswith(homepath):
        return os.path.join('~', fullpath[len(homepath):])
    return fullpath


def get_nonempty_list(elem):
    # FIXME: get rid of that, or explain. It makes no sense...
    if not elem:
        return None
    elif isinstance(elem, (list, tuple)):
        return elem
    else:
        return [elem]


def get_gm_attributes(plot_type):
    """Return the list of "graphics method attributes" for a given plot type.
    """
    if plot_type == "Boxfill":
        return ['boxfill_type', 'color_1', 'color_2', 'datawc_calendar',
                'datawc_timeunits', 'datawc_x1', 'datawc_x2', 'datawc_y1',
                'datawc_y2', 'levels', 'ext_1', 'ext_2', 'fillareacolors',
                'fillareaindices', 'fillareastyle', 'legend', 'level_1',
                'level_2', 'missing', 'projection', 'xaxisconvert', 'xmtics1',
                'xmtics2', 'xticlabels1', 'xticlabels2', 'yaxisconvert',
                'ymtics1', 'ymtics2', 'yticlabels1', 'yticlabels2']

    elif plot_type == "3D_Scalar" or plot_type == "3D_Dual_Scalar":
        from DV3D.ConfigurationFunctions import ConfigManager
        from DV3D.DV3DPlot import PlotButtonNames
        cfgManager = ConfigManager()
        parameterList = cfgManager.getParameterList(extras=(['axes'] +
                                                            PlotButtonNames))
        return parameterList

    elif plot_type == "3D_Vector":
        from DV3D.ConfigurationFunctions import ConfigManager
        from DV3D.DV3DPlot import PlotButtonNames
        cfgManager = ConfigManager()
        parameterList = cfgManager.getParameterList(extras=(['axes'] +
                                                            PlotButtonNames))
        return parameterList

    elif plot_type == "Isofill":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'levels', 'ext_1',
                'ext_2', 'fillareacolors', 'fillareaindices', 'fillareastyle',
                'legend', 'missing', 'projection', 'xaxisconvert', 'xmtics1',
                'xmtics2', 'xticlabels1', 'xticlabels2', 'yaxisconvert',
                'ymtics1', 'ymtics2', 'yticlabels1', 'yticlabels2']

    elif plot_type == "Isoline":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'projection',
                'xaxisconvert', 'xmtics1', 'xmtics2', 'xticlabels1',
                'xticlabels2', 'yaxisconvert', 'ymtics1', 'ymtics2',
                'yticlabels1', 'yticlabels2', 'label', 'level', 'levels',
                'line', 'linecolors', 'linewidths', 'text', 'textcolors',
                'clockwise', 'scale', 'angle', 'spacing']
    elif plot_type == "Meshfill":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'levels', 'ext_1',
                'ext_2', 'fillareacolors', 'fillareaindices', 'fillareastyle',
                'legend', 'missing', 'projection', 'xaxisconvert', 'xmtics1',
                'xmtics2', 'xticlabels1', 'xticlabels2', 'yaxisconvert',
                'ymtics1', 'ymtics2', 'yticlabels1', 'yticlabels2', 'mesh',
                'wrap']
    elif plot_type == "Scatter":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'markercolor', 'marker',
                'markersize', 'projection', 'xaxisconvert', 'xmtics1',
                'xmtics2', 'xticlabels1', 'xticlabels2', 'yaxisconvert',
                'ymtics1', 'ymtics2', 'yticlabels1', 'yticlabels2']
    elif plot_type == "Vector":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'linecolor', 'line',
                'linewidth', 'scale', 'alignment', 'type', 'reference',
                'projection', 'xaxisconvert', 'xmtics1', 'xmtics2',
                'xticlabels1', 'xticlabels2', 'yaxisconvert', 'ymtics1',
                'ymtics2', 'yticlabels1', 'yticlabels2']
    elif plot_type == "XvsY":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'linecolor', 'line',
                'linewidth', 'markercolor', 'marker', 'markersize',
                'projection', 'xaxisconvert', 'xmtics1', 'xmtics2',
                'xticlabels1', 'xticlabels2', 'yaxisconvert', 'ymtics1',
                'ymtics2', 'yticlabels1', 'yticlabels2']
    elif plot_type == "Xyvsy":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'linecolor', 'line',
                'linewidth', 'markercolor', 'marker', 'markersize',
                'projection', 'xmtics1', 'xmtics2', 'xticlabels1',
                'xticlabels2', 'yaxisconvert', 'ymtics1', 'ymtics2',
                'yticlabels1', 'yticlabels2']
    elif plot_type == "Yxvsx":
        return ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                'datawc_x2', 'datawc_y1', 'datawc_y2', 'linecolor', 'line',
                'linewidth', 'markercolor', 'marker', 'markersize',
                'projection', 'xmtics1', 'xmtics2', 'xticlabels1',
                'xticlabels2', 'xaxisconvert', 'ymtics1', 'ymtics2',
                'yticlabels1', 'yticlabels2']
    elif plot_type == "Taylordiagram":
        return ['detail', 'max', 'quadrans', 'skillValues', 'skillColor',
                'skillDrawLabels', 'skillCoefficient', 'referencevalue',
                'arrowlength', 'arrowangle', 'arrowbase', 'xmtics1',
                'xticlabels1', 'ymtics1', 'yticlabels1', 'cmtics1',
                'cticlabels1', 'Marker']
    else:
        debug.warning("Unable to get gm attributes for plot type %s" %
                      plot_type)


# Some VCS operations can only be called on a canvas, we create a global one
# that will not be used for plotting, only to get various attributes
# FIXME vcs: These should probably be accessible globally, without a Canvas
global_canvas = vcs.init()


# List of default attributes for a plot type and graphics method
# This is used by DAT to set the default values on a newly created plot
# TODO: make DAT use it
# FIXME: there is no easy way to change all of these when changing graphics
# FIXME: method. But it looks like they don't depend on the GM, only the plot
# FIXME: type...
# FIXME: also, should probably just be the module's default values
# FIXME: This is insane and we probably just want to get rid of it
original_gm_attributes = {}

for plot_type in ['Boxfill', 'Isofill', 'Isoline', 'Meshfill', 'Scatter',
                  'Taylordiagram', 'Vector', 'XvsY', 'Xyvsy', 'Yxvsx',
                  '3D_Dual_Scalar', '3D_Scalar', '3D_Vector']:
    method_name = "get" + plot_type.lower()
    attributes = get_gm_attributes(plot_type)
    gms = global_canvas.listelements(str(plot_type).lower())
    original_gm_attributes[plot_type] = {}
    for gmname in gms:
        gm = getattr(global_canvas, method_name)(gmname)
        attrs = {}
        for attr in attributes:
            attrs[attr] = getattr(gm, attr)
            if attr == 'linecolor' and attrs[attr] is None:
                attrs[attr] = 241
            elif attr == 'linewidth' and attrs[attr] is None:
                attrs[attr] = 1
            elif attr == 'line' and attrs[attr] is None:
                attrs[attr] = 'solid'
            elif attr == 'markercolor' and attrs[attr] is None:
                attrs[attr] = 241
            elif attr == 'markersize' and attrs[attr] is None:
                attrs[attr] = 1
            elif attr == 'marker' and attrs[attr] is None:
                attrs[attr] = 'dot'
            elif attr == 'max' and attrs[attr] is None:
                attrs[attr] = 1
        original_gm_attributes[plot_type][gmname] = attrs


class VariableSource(Module):
    # FIXME: needed?
    _input_ports = [("file", "basic:File"),
                    ("url", "basic:String")]
    _output_ports = [("variables", "basic:List"),
                     ("dimensions", "basic:List"),
                     ("attributes", "basic:List")]


class CDMSVariable(Module):
    """CDMS variable loader.

    This can get turned into an actual CDMS variable with to_python().
    """
    _input_ports = [("file", "basic:File"),
                    ("url", "basic:String"),
                    ("source", "VariableSource"),
                    ("name", "basic:String"),
                    ("load", "basic:Boolean"),
                    ("axes", "basic:String"),
                    ("axesOperations", "basic:String"),
                    ("varNameInFile", "basic:String"),
                    ("attributes", "basic:Dictionary"),
                    ("axisAttributes", "basic:Dictionary"),
                    ("setTimeBounds", "basic:String")]
    _output_ports = [("attributes", "basic:Dictionary"),
                     ("dimensions", "basic:List"),
                     ("self", "CDMSVariable")]

    def __init__(self, filename=None, url=None, source=None, name=None,
                 load=False, varNameInFile=None, axes=None,
                 axesOperations=None, attributes=None, axisAttributes=None,
                 timeBounds=None):
        Module.__init__(self)
        self.filename = filename
        self.url = url
        self.source = source
        self.name = name
        self.load = load
        self.file = self.filename
        self.relativize_paths()

        self.axes = axes
        self.axesOperations = axesOperations
        self.varNameInFile = varNameInFile
        self.attributes = attributes
        self.axisAttributes = axisAttributes
        self.timeBounds = timeBounds
        self.var = None

        if varNameInFile is None:
            self.varname = name
        else:
            self.varname = varNameInFile

    def relativize_paths(self):
        self.file = unexpand_home_path(self.file)
        self.url = unexpand_home_path(self.url)

    def get_port_values(self):
        if (not self.hasInputFromPort('file') and
                not self.hasInputFromPort('url') and
                not self.hasInputFromPort('source')):
            raise ModuleError(self,
                              "Must set one of 'file', 'url', 'source'.")
        if self.hasInputFromPort('file'):
            self.file = self.getInputFromPort('file').name
            self.filename = self.file
        if self.hasInputFromPort('url'):
            self.url = self.getInputFromPort('url')
        if self.hasInputFromPort('source'):
            self.source = self.getInputFromPort('source')
        self.name = self.getInputFromPort('name')
        self.load = self.forceGetInputFromPort('load', False)
        self.relativize_paths()

    def __copy__(self):
        cp = CDMSVariable()
        cp.filename = self.filename
        cp.file = self.file
        cp.url = self.url
        cp.source = self.source
        cp.name = self.name
        cp.load = self.load
        cp.varNameInFile = self.varNameInFile
        cp.varname = self.varname
        cp.axes = self.axes
        cp.axesOperations = self.axesOperations
        cp.attributes = self.attributes
        cp.axisAttributes = self.axisAttributes
        cp.timeBounds = self.timeBounds
        return cp

    def to_python(self):
        """Actually loads the variable from the file, and return it.
        """
        if self.source:
            cdmsfile = self.source.var
        elif self.url:
            url_path = os.path.expanduser(self.url)
            cdmsfile = cdms2.open(os.path.expanduser(url_path))
        elif self.file:
            file_path = os.path.expanduser(self.file)
            cdmsfile = cdms2.open(file_path)
        else:
            assert False

        varName = self.name
        if self.varNameInFile is not None:
            varName = self.varNameInFile

        # get file var to see if it is axis or not
        fvar = cdmsfile[varName]
        if isinstance(fvar, cdms2.axis.FileAxis):
            var = cdms2.MV2.array(fvar)

            # convert string into kwargs
            # example axis string:
            # lon=(0.0, 358.5),lev=(3.54, 992.55),
            # time=('301-1-1 0:0:0.0', '301-2-1 0:0:0.0'),lat=(-88.92, 88.92),
            # squeeze=1,
            if self.axes is not None:
                assert isinstance(fvar, cdms2.axis.FileAxis)

                try:
                    kwargs = eval('dict(%s)' % self.axes)
                except Exception as e:
                    raise ModuleError(
                        self,
                        "Invalid 'axes' specification: %s\n"
                        "Produced error: %s" % (self.axes, str(e)))

                if isinstance(fvar, cdms2.axis.FileAxis):
                    try:
                        var = var(**kwargs)
                    except Exception as e:
                        debug.warning(
                            "WARNING: axis variable %s subslice failed with "
                            "selector '%r'\nError: %s" % (varName, kwargs, e))
                else:
                    var = cdmsfile(varName, **kwargs)
        elif not isinstance(fvar, cdms2.axis.FileAxis):
            var = cdmsfile(varName)
        else:
            raise ModuleError(self, "Unknown variable type: %s" % type(fvar))

        if self.axesOperations is not None:
            var = CDMSVariable.applyAxesOperations(var, self.axesOperations)

        # make sure that var.id is the same as self.name
        var.id = self.name
        if self.attributes is not None:
            for attr in self.attributes:
                try:
                    attValue = eval(str(self.attributes[attr]))
                except:
                    attValue = str(self.attributes[attr])
                setattr(var, attr, attValue)

        if self.axisAttributes is not None:
            for axName in self.axisAttributes:
                for attr in self.axisAttributes[axName]:
                    try:
                        attValue = eval(str(self.axisAttributes[axName][attr]))
                    except:
                        attValue = str(self.axisAttributes[axName][attr])
                    ax = var.getAxis(var.getAxisIndex(axName))
                    setattr(ax, attr, attValue)

        if self.timeBounds is not None:
            var = self.applySetTimeBounds(var, self.timeBounds)

        return var

    def compute(self):
        self.axes = self.forceGetInputFromPort("axes")
        self.axesOperations = self.forceGetInputFromPort("axesOperations")
        self.varNameInFile = self.forceGetInputFromPort("varNameInFile")
        if self.varNameInFile is not None:
            self.varname = self.varNameInFile
        self.attributes = self.forceGetInputFromPort("attributes")
        self.axisAttributes = self.forceGetInputFromPort("axisAttributes")
        self.timeBounds = self.forceGetInputFromPort("setTimeBounds")
        self.get_port_values()
        self.var = self.to_python()
        self.setResult("self", self)

    @staticmethod
    def applyAxesOperations(var, axesOperations):
        """ Apply axes operations to update the slab """
        try:
            axesOperations = ast.literal_eval(axesOperations)
        except:
            raise TypeError("Invalid string 'axesOperations': %r" %
                            axesOperations)

        for axis in list(axesOperations):
            if axesOperations[axis] == 'sum':
                var = cdutil.averager(var, axis="(%s)" % axis, weight='equal',
                                      action='sum')
            elif axesOperations[axis] == 'avg':
                var = cdutil.averager(var, axis="(%s)" % axis, weight='equal')
            elif axesOperations[axis] == 'wgt':
                var = cdutil.averager(var, axis="(%s)" % axis)
            elif axesOperations[axis] == 'gtm':
                var = genutil.statistics.geometricmean(var, axis="(%s)" % axis)
            elif axesOperations[axis] == 'std':
                var = genutil.statistics.std(var, axis="(%s)" % axis)
        return var

    @staticmethod
    def applySetTimeBounds(var, timeBounds):
        data = timeBounds.split(":", 1)
        val = None
        if len(data) == 2:
            timeBounds = data[0]
            val = float(data[1])
        if timeBounds == "Set Bounds For Yearly Data":
            cdutil.times.setTimeBoundsYearly(var)
        elif timeBounds == "Set Bounds For Monthly Data":
            cdutil.times.setTimeBoundsMonthly(var)
        elif timeBounds == "Set Bounds For Daily Data":
            cdutil.times.setTimeBoundsDaily(var)
        elif timeBounds == "Set Bounds For Twice-daily Data":
            cdutil.times.setTimeBoundsDaily(var, 2)
        elif timeBounds == "Set Bounds For 6-Hourly Data":
            cdutil.times.setTimeBoundsDaily(var, 4)
        elif timeBounds == "Set Bounds For Hourly Data":
            cdutil.times.setTimeBoundsDaily(var, 24)
        elif timeBounds == "Set Bounds For X-Daily Data":
            assert val is not None
            cdutil.times.setTimeBoundsDaily(var, val)
        return var


class CDMSVariableOperation(Module):
    _input_ports = [("varname", "basic:String"),
                    ("python_command", "basic:String"),
                    ("axes", "basic:String"),
                    ("axesOperations", "basic:String"),
                    ("attributes", "basic:Dictionary"),
                    ("axisAttributes", "basic:Dictionary"),
                    ("timeBounds", "basic:String")]

    _output_ports = [("output_var", "CDMSVariable")]

    def __init__(self, varname=None, python_command=None, axes=None,
                 axesOperations=None, attributes=None, axisAttributes=None,
                 timeBounds=None):
        Module.__init__(self)
        self.varname = varname
        self.python_command = python_command
        self.axes = axes
        self.axesOperations = axesOperations
        self.attributes = attributes
        self.axisAttributes = axisAttributes
        self.timeBounds = timeBounds

    def get_port_values(self):
        if not self.hasInputFromPort("varname"):
            raise ModuleError(self, "'varname' is mandatory.")
        if not self.hasInputFromPort("python_command"):
            raise ModuleError(self, "'python_command' is mandatory.")
        self.varname = self.forceGetInputFromPort("varname")
        self.python_command = self.getInputFromPort("python_command")
        self.axes = self.forceGetInputFromPort("axes")
        self.axesOperations = self.forceGetInputFromPort("axesOperations")
        self.attributes = self.forceGetInputFromPort("attributes")
        self.axisAttributes = self.forceGetInputFromPort("axisAttributes")
        self.timeBounds = self.forceGetInputFromPort("timeBounds")

    @staticmethod
    def find_variable_in_command(v, command, startpos=0):
        """find_variable(v:str,command:str) -> int
        find the first occurrence of v in command, respecting identifier
        names
        Examples:
        >>> find_variable = CDMSVariableOperation.find_variable_in_command
        >>> find_variable("v", "av = clt * 2")
        -1
        >>> find_variable("var", "self.var = 3 * clt"
        -1
        """
        bidentchars = string.letters + string.digits + '_.'
        aidentchars = string.letters + string.digits + '_'
        i = command.find(v, startpos)
        if i < 0:  # not found
            return i
        # checking before and after
        before = i - 1
        after = i + len(v)
        ok_before = True
        ok_after = True
        if before >= 0:
            if command[before] in bidentchars:
                ok_before = False

        if after < len(command):
            if command[after] in aidentchars:
                ok_after = False

        if ok_after and ok_before:
            return i
        else:
            spos = i + len(v)
            while spos < len(command) - 1 and command[spos] in aidentchars:
                spos += 1
            return CDMSVariableOperation.find_variable_in_command(v, command,
                                                                  spos)

    @staticmethod
    def replace_variable_in_command(command, oldv, newv):
        newcommand = ""
        changedcommand = command
        i = CDMSVariableOperation.find_variable_in_command(oldv,
                                                           changedcommand)
        while i > -1:
            newcommand += changedcommand[:i]
            newcommand += newv
            changedcommand = changedcommand[i + len(oldv):]
            i = CDMSVariableOperation.find_variable_in_command(oldv,
                                                               changedcommand)
        newcommand += changedcommand
        return newcommand

    def compute(self):
        pass

    def set_variables(self, vars):
        pass

    def applyOperations(self, var):
        if self.axes is not None:
            try:
                var = eval("var(%s)" % self.axes)
            except Exception, e:
                raise ModuleError(self, "Invalid 'axes' specification: %s" % e)
        if self.axesOperations is not None:
            var = CDMSVariable.applyAxesOperations(var, self.axesOperations)

        if self.attributes is not None:
            for attr in self.attributes:
                try:
                    attValue = eval(str(self.attributes[attr]))
                except:
                    attValue = str(self.attributes[attr])
                setattr(var, attr, attValue)

        if self.axisAttributes is not None:
            for axName in self.axisAttributes:
                for attr in self.axisAttributes[axName]:
                    try:
                        attValue = eval(str(self.axisAttributes[axName][attr]))
                    except:
                        attValue = str(self.axisAttributes[axName][attr])
                    ax = var.getAxis(var.getAxisIndex(axName))
                    setattr(ax, attr, attValue)

        if self.timeBounds is not None:
            var = CDMSVariable.applySetTimeBounds(var, self.timeBounds)
        return var


class CDMSUnaryVariableOperation(CDMSVariableOperation):
    _input_ports = [("input_var", "CDMSVariable")]

    def __init__(self, varname=None, python_command=None, axes=None,
                 axesOperations=None, attributes=None, axisAttributes=None,
                 timeBounds=None):
        CDMSVariableOperation.__init__(self, varname, python_command, axes,
                                       axesOperations, attributes,
                                       axisAttributes, timeBounds)
        self.var = None

    def to_python(self):
        self.python_command = self.replace_variable_in_command(
            self.python_command, self.var.name, "self.var.var")

        res = eval(self.python_command)

        if type(res) == tuple:
            for r in res:
                if isinstance(r, cdms2.tvariable.TransientVariable):
                    var = r
                    break
            else:
                raise ModuleError(self,
                                  "Command didn't return a TransientVariable")
        else:
            var = res

        if isinstance(var, cdms2.tvariable.TransientVariable):
            var.id = self.varname
            var = self.applyOperations(var)
        return var

    def compute(self):
        if not self.hasInputFromPort('input_var'):
            raise ModuleError(self, "'input_var' is mandatory.")

        self.var = self.getInputFromPort('input_var')
        self.get_port_values()
        self.outvar = CDMSVariable(filename=None, name=self.varname)
        self.outvar.var = self.to_python()
        self.setResult("output_var", self.outvar)

    def set_variables(self, vars):
        self.var = vars[0]


class CDMSBinaryVariableOperation(CDMSVariableOperation):
    _input_ports = [("input_var1", "CDMSVariable"),
                    ("input_var2", "CDMSVariable")]

    def __init__(self, varname=None, python_command=None, axes=None,
                 axesOperations=None, attributes=None, axisAttributes=None,
                 timeBounds=None):
        CDMSVariableOperation.__init__(self, varname, python_command, axes,
                                       axesOperations, attributes,
                                       axisAttributes, timeBounds)
        self.var1 = None
        self.var2 = None

    def compute(self):
        if not self.hasInputFromPort('input_var1'):
            raise ModuleError(self, "'input_var1' is mandatory.")

        if not self.hasInputFromPort('input_var2'):
            raise ModuleError(self, "'input_var2' is mandatory.")

        self.var1 = self.getInputFromPort('input_var1')
        self.var2 = self.getInputFromPort('input_var2')
        self.get_port_values()
        self.outvar = CDMSVariable(filename=None, name=self.varname)
        self.outvar.var = self.to_python()
        self.setResult("output_var", self.outvar)

    def set_variables(self, vars):
        self.var1 = vars[0]
        self.var2 = vars[1]

    def to_python(self):
        replace_map = {self.var1.name: "self.var1.var",
                       self.var2.name: "self.var2.var"}

        vars = [self.var1, self.var2]
        for v in vars:
            self.python_command = self.replace_variable_in_command(
                self.python_command, v.name, replace_map[v.name])

        res = eval(self.python_command)
        if type(res) == tuple:
            for r in res:
                if isinstance(r, cdms2.tvariable.TransientVariable):
                    var = r
                    break
            else:
                raise ModuleError(self,
                                  "Command didn't return a TransientVariable")
        else:
            var = res

        if isinstance(var, cdms2.tvariable.TransientVariable):
            var.id = self.varname
            var = self.applyOperations(var)
        return var


class CDMSGrowerOperation(CDMSBinaryVariableOperation):

    _input_ports = [("varname2", "basic:String")]

    _output_ports = [("output_var", "CDMSVariable"),
                     ("output_var2", "CDMSVariable")]

    def compute(self):
        if not self.hasInputFromPort('input_var1'):
            raise ModuleError(self, "'input_var1' is mandatory.")

        if not self.hasInputFromPort('input_var2'):
            raise ModuleError(self, "'input_var2' is mandatory.")

        self.var1 = self.getInputFromPort('input_var1')
        self.var2 = self.getInputFromPort('input_var2')
        self.get_port_values()
        self.outvar = CDMSVariable(filename=None, name=self.varname)
        self.outvar2 = CDMSVariable(filename=None, name=self.varname2)
        self.outvar.var = self.to_python()
        self.outvar2.var = self.result2
        self.setResult("output_var", self.outvar)
        self.setResult("output_var2", self.outvar2)

    def get_port_values(self):
        if not self.hasInputFromPort("varname"):
            raise ModuleError(self, "'varname' is mandatory.")
        if not self.hasInputFromPort("varname2"):
            raise ModuleError(self, "'varname2' is mandatory.")
        if not self.hasInputFromPort("python_command"):
            raise ModuleError(self, "'python_command' is mandatory.")
        self.varname = self.forceGetInputFromPort("varname")
        self.varname2 = self.forceGetInputFromPort("varname2")
        self.python_command = self.getInputFromPort("python_command")
        self.axes = self.forceGetInputFromPort("axes")
        self.axesOperations = self.forceGetInputFromPort("axesOperations")
        self.attributes = self.forceGetInputFromPort("attributes")
        self.axisAttributes = self.forceGetInputFromPort("axisAttributes")
        self.timeBounds = self.forceGetInputFromPort("timeBounds")

    def to_python(self):
        replace_map = {self.var1.name: "self.var1.var",
                       self.var2.name: "self.var2.var"}

        vars = [self.var1, self.var2]
        for v in vars:
            self.python_command = self.replace_variable_in_command(
                self.python_command, v.name, replace_map[v.name])

        res = eval(self.python_command)
        if type(res) != tuple:
            raise ModuleError(self,
                              "Expecting tuple output from grower, got %s "
                              "instead." % type(res))
        elif len(res) != 2:
            raise ModuleError(self, "Expecting 2 outputs from grower, got %d "
                                    "instead." % len(res))

        var = res[0]
        var.id = self.varname
        var = self.applyOperations(var)

        self.result2 = res[1]
        self.result2.id = self.varname2
        self.result2 = self.applyOperations(self.result2)

        return var


class CDMSNaryVariableOperation(CDMSVariableOperation):
    _input_ports = [("input_vars", "CDMSVariable")]

    def __init__(self, varname=None, python_command=None, axes=None,
                 axesOperations=None, attributes=None, axisAttributes=None,
                 timeBounds=None):
        CDMSVariableOperation.__init__(self, varname, python_command, axes,
                                       axesOperations, attributes,
                                       axisAttributes, timeBounds)
        self.vars = None

    def compute(self):
        if self.hasInputFromPort('input_vars'):
            self.vars = self.getInputListFromPort('input_vars')
        else:
            self.vars = []
        self.get_port_values()
        self.outvar = CDMSVariable(filename=None, name=self.varname)
        self.outvar.var = self.to_python()
        self.setResult("output_var", self.outvar)

    def set_variables(self, vars):
        for v in vars:
            self.vars.append(v)

    def to_python(self):
        replace_map = {}
        for i in range(len(self.vars)):
            replace_map[self.vars[i].name] = "self.vars[%s].var" % i

        for v in self.vars:
            self.python_command = self.replace_variable_in_command(
                self.python_command, v.name, replace_map[v.name])

        res = eval(self.python_command)
        if type(res) == tuple:
            for r in res:
                if isinstance(r, cdms2.tvariable.TransientVariable):
                    var = r
                    break
            else:
                raise ModuleError(self,
                                  "Command didn't return a TransientVariable")
        else:
            var = res

        if isinstance(var, cdms2.tvariable.TransientVariable):
            var.id = self.varname
            var = self.applyOperations(var)
        return var


class CDMSPlot(Module, NotCacheable):
    _input_ports = [("variable", "CDMSVariable")]

    def __init__(self):
        Module.__init__(self)
        self.var = None


class CDMS3DPlot(CDMSPlot):
    _input_ports = [("variable", "CDMSVariable"),
                    ("variable2", "CDMSVariable", True),
                    ("plotOrder", "basic:Integer", True),
                    ("graphicsMethodName", "basic:String"),
                    ("template", "basic:String")]
    _output_ports = [("self", "CDMS3DPlot")]

    gm_attributes = ['projection']

    plot_type = None

    def __init__(self):
        CDMSPlot.__init__(self)

        NotCacheable.__init__(self)
        self.template = "starter"
        self.graphics_method_name = "default"
        self.kwargs = {}
        self.plot_order = -1
        self.default_values = {}
        self.colorMap = None

    def compute(self):
        import vcs
        self.var = self.getInputFromPort('variable').var
        self.setResult("self", self)
        self.graphics_method_name = self.forceGetInputFromPort(
            "graphicsMethodName", "default")
        #self.set_default_values()
        self.template = self.forceGetInputFromPort("template", "starter")

        if not self.hasInputFromPort('variable'):
            raise ModuleError(self, "'variable' is mandatory.")
        self.var = self.getInputFromPort('variable')

        self.var2 = None
        if self.hasInputFromPort('variable2'):
            self.var2 = self.getInputFromPort('variable2')

        if self.hasInputFromPort("plotOrder"):
            self.plot_order = self.getInputFromPort("plotOrder")

        #pipeline = self.moduleInfo['pipeline']
        #cell_coords = CDMSPipelineHelper.getCellLoc(pipeline)

        gm = vcs.elements[self.plot_type.lower()][self.graphics_method_name]
        for attr in self.gm_attributes:
            if self.hasInputFromPort(attr):
                value = self.getInputFromPort(attr)
                if isinstance(value, str):
                    try:
                        value = ast.literal_eval(value)
                    except ValueError:
                        pass
                values = get_nonempty_list(value)
                if values is not None:
                    for value in values:
                        if value == "vcs.on":
                            gm.setParameter(attr, None, state=1)
                        elif value == "vcs.off":
                            gm.setParameter(attr, None, state=0)
                    setattr(self, attr, values)
                    #gm.setParameter( attr, values, cell=cell_coords )

    def set_default_values(self, gmName=None):
        self.default_values = {}
        if gmName is None:
            gmName = self.graphics_method_name
        if self.plot_type is not None:
            method_name = "get" + str(self.plot_type).lower()
            gm = getattr(global_canvas, method_name)(gmName)
            for attr in self.gm_attributes:
                setattr(self, attr, getattr(gm, attr))
                self.default_values[attr] = getattr(gm, attr)

    @staticmethod
    def get_canvas_graphics_method(plotType, gmName):
        method_name = "get" + str(plotType).lower()
        return getattr(global_canvas, method_name)(gmName)

    @classmethod
    def addPlotPorts(cls):
        from vcs.dv3d import Gfdv3d
        plist = Gfdv3d.getParameterList()
        reg = get_module_registry()
        pkg_identifier = None
        for pname in plist:
            cls.gm_attributes.append(pname)
            cls._input_ports.append(
                (pname,
                 reg.expand_port_spec_string("basic:String", pkg_identifier),
                 True))


class CDMS2DPlot(CDMSPlot):
    _input_ports = [("variable", "CDMSVariable"),
                    ("variable2", "CDMSVariable", True),
                    ("plotOrder", "basic:Integer", True),
                    ("graphicsMethodName", "basic:String"),
                    ("template", "basic:String"),
                    ('datawc_calendar', 'basic:Integer', True),
                    ('datawc_timeunits', 'basic:String', True),
                    ('datawc_x1', 'basic:Float', True),
                    ('datawc_x2', 'basic:Float', True),
                    ('datawc_y1', 'basic:Float', True),
                    ('datawc_y2', 'basic:Float', True),
                    ('xticlabels1', 'basic:String', True),
                    ('xticlabels2', 'basic:String', True),
                    ('yticlabels1', 'basic:String', True),
                    ('yticlabels2', 'basic:String', True),
                    ('xmtics1', 'basic:String', True),
                    ('xmtics2', 'basic:String', True),
                    ('ymtics1', 'basic:String', True),
                    ('ymtics2', 'basic:String', True),
                    ('projection', 'basic:String', True),
                    ('continents', 'basic:Integer', True),
                    ('ratio', 'basic:String', True),
                    ("colorMap", "CDMSColorMap", True)]
    _output_ports = [("self", "CDMS2DPlot")]

    gm_attributes = ['datawc_calendar', 'datawc_timeunits', 'datawc_x1',
                     'datawc_x2', 'datawc_y1', 'datawc_y2', 'xticlabels1',
                     'xticlabels2', 'yticlabels1', 'yticlabels2', 'xmtics1',
                     'xmtics2', 'ymtics1', 'ymtics2', 'projection']

    plot_type = None

    def __init__(self):
        CDMSPlot.__init__(self)

        self.template = "starter"
        self.graphics_method_name = "default"
        self.plot_order = -1
        self.kwargs = {}
        self.default_values = {}

    def compute(self):
        self.var = self.getInputFromPort('variable').var
        self.setResult("self", self)

        self.graphics_method_name = \
            self.forceGetInputFromPort("graphicsMethodName", "default")
        #self.set_default_values()
        self.template = self.forceGetInputFromPort("template", "starter")

        if not self.hasInputFromPort('variable'):
            raise ModuleError(self, "'variable' is mandatory.")
        self.var = self.getInputFromPort('variable')

        self.var2 = None
        if self.hasInputFromPort('variable2'):
            self.var2 = self.getInputFromPort('variable2')

        if self.hasInputFromPort("plotOrder"):
            self.plot_order = self.getInputFromPort("plotOrder")

        for attr in self.gm_attributes:
            if self.hasInputFromPort(attr):
                setattr(self, attr, self.getInputFromPort(attr))
                if attr == 'Marker':
                    setattr(self, attr, pickle.loads(getattr(self, attr)))

        self.colorMap = None
        if self.hasInputFromPort('colorMap'):
            self.colorMap = self.getInputFromPort('colorMap')

        self.kwargs['continents'] = 1
        if self.hasInputFromPort('continents'):
            self.kwargs['continents'] = self.getInputFromPort('continents')

        self.kwargs['ratio'] = 'autot'
        if self.hasInputFromPort('ratio'):
            self.kwargs['ratio'] = self.getInputFromPort('ratio')
            if self.kwargs['ratio'] != 'autot':
                try:
                    float(self.kwargs['ratio'])
                except ValueError:
                    self.kwargs['ratio'] = 'autot'

    def set_default_values(self, gmName=None):
        self.default_values = {}
        if gmName is None:
            gmName = self.graphics_method_name
        if self.plot_type is not None:
            method_name = "get" + str(self.plot_type).lower()
            gm = getattr(global_canvas, method_name)(gmName)
            for attr in self.gm_attributes:
                setattr(self, attr, getattr(gm, attr))
                self.default_values[attr] = getattr(gm, attr)

    @staticmethod
    def get_canvas_graphics_method(plotType, gmName):
        method_name = "get" + str(plotType).lower()
        return getattr(global_canvas, method_name)(gmName)


class CDMSTDMarker(Module):
    _input_ports = [("status", "basic:List", True),
                    ("line", "basic:List", True),
                    ("id", "basic:List", True),
                    ("id_size", "basic:List", True),
                    ("id_color", "basic:List", True),
                    ("id_font", "basic:List", True),
                    ("symbol", "basic:List", True),
                    ("color", "basic:List", True),
                    ("size", "basic:List", True),
                    ("xoffset", "basic:List", True),
                    ("yoffset", "basic:List", True),
                    ("linecolor", "basic:List", True),
                    ("line_size", "basic:List", True),
                    ("line_type", "basic:List", True)]
    _output_ports = [("self", "CDMSTDMarker")]


class CDMSColorMap(Module):
    _input_ports = [("colorMapName", "basic:String"),
                    ("colorCells", "basic:List")]
    _output_ports = [("self", "CDMSColorMap")]

    def __init__(self):
        Module.__init__(self)
        self.colorMapName = None
        self.colorCells = None

    def compute(self):
        self.colorMapName = self.forceGetInputFromPort('colorMapName')
        self.colorCells = self.forceGetInputFromPort("colorCells")
        self.setResult("self", self)


class CDMSCell(SpreadsheetCell):
    _input_ports = [("plot", "CDMSPlot")]

    def __init__(self, *args, **kargs):
        SpreadsheetCell.__init__(self)

    def compute(self):
        input_ports = []
        plots = []
        for plot in sorted(self.getInputListFromPort('plot'),
                           key=lambda obj: obj.plot_order):
            plots.append(plot)
        input_ports.append(plots)
        self.cellWidget = self.displayAndWait(QCDATWidget, input_ports)


class QCDATWidget(QVTKWidget):
    """ QCDATWidget is the spreadsheet cell widget where the plots are displayed.
    The widget interacts with the underlying C++, VCSQtManager through SIP.
    This enables QCDATWidget to get a reference to the Qt MainWindow that the
    plot will be displayed in and send signals (events) to that window widget.
    windowIndex is an index to the VCSQtManager window array so we can
    communicate with the C++ Qt windows which the plots show up in.  If this
    number is no longer consistent with the number of C++ Qt windows due to
    adding or removing vcs.init() calls, then when you plot, it will plot into
    a separate window instead of in the cell and may crash.
    vcdat already creates 5 canvas objects

    """
    save_formats = ["PNG file (*.png)",
                    "GIF file (*.gif)",
                    "PDF file (*.pdf)",
                    "Postscript file (*.ps)",
                    "SVG file (*.svg)"]

    # this should be the current number of canvas objects created
    #startIndex = 2
    #maxIndex = 9999999999
    #usedIndexes = []

    def __init__(self, parent=None):
        QVTKWidget.__init__(self, parent)
        # self.window = None
        self.canvas = None
        #self.windowId = -1
        #self.createCanvas()
        #layout = QtGui.QVBoxLayout()
        #self.setLayout(layout)

    def createCanvas(self):
        if self.canvas is not None:
            return

        self.canvas = vcs.init(backend=self.GetRenderWindow())
        ren = vtk.vtkRenderer()
        r, g, b = self.canvas.backgroundcolor
        ren.SetBackground(r / 255., g / 255., b / 255.)
        self.canvas.backend.renWin.AddRenderer(ren)
        self.canvas.backend.createDefaultInteractor()
        i = self.canvas.backend.renWin.GetInteractor()
        i.RemoveObservers("ConfigureEvent")
        try:
            i.RemoveObservers("ModifiedEvent")
        except:
            pass
        i.AddObserver("ModifiedEvent", self.canvas.backend.configureEvent)

    def prepExtraDims(self, var):
        k = {}
        for d, i in zip(self.extraDimsNames, self.extraDimsIndex):
            if d in var.getAxisIds():
                k[d] = slice(i, None)
        return k

    def updateContents(self, inputPorts, fromToolBar=False):
        """ Get the vcs canvas, setup the cell's layout, and plot """
        self.createCanvas()

        spreadsheetWindow = spreadsheetController.findSpreadsheetWindow()
        spreadsheetWindow.setUpdatesEnabled(False)
        # Set the canvas
        # if inputPorts[0] is not None:
        #     self.canvas = inputPorts[0]
        #self.window = self.canvas
        if self.canvas is None:
            try:
                self.createCanvas()
            except ModuleError, e:
                spreadsheetWindow.setUpdatesEnabled(True)
                raise e

        #get reparented window if it's there
        #if self.windowId in reparentedVCSWindows:
        #    self.window = reparentedVCSWindows[self.windowId]
        #    del reparentedVCSWindows[self.windowId]
        #else:
        #    self.window = self.canvas

        #self.layout().addWidget(self.window)
        #self.window.setVisible(True)
        # Place the mainwindow that the plot will be displayed in, into this
        # cell widget's layout

        self.canvas.clear()
        if not fromToolBar:
            self.extraDimsNames = inputPorts[0][0].var.var.getAxisIds()[:-2]
            self.extraDimsIndex = [0] * len(self.extraDimsNames)
            self.extraDimsLen = inputPorts[0][0].var.var.shape[:-2]
            self.inputPorts = inputPorts
            if hasattr(self.parent(), "toolBar"):
                t = self.parent().toolBar
                if hasattr(t, "dimSelector"):
                    while (t.dimSelector.count() > 0):
                        t.dimSelector.removeItem(0)
                    t.dimSelector.addItems(self.extraDimsNames)
        # Plot
        for plot in inputPorts[0]:
            cmd = "# Now plotting\nvcs_canvas[%i].plot(" % (
                self.canvas.canvasid() - 1)
            k1 = self.prepExtraDims(plot.var.var)
            args = [plot.var.var(**k1)]
            cmd += "%s(**%s), " % (args[0].id, str(k1))
            if hasattr(plot, "var2") and plot.var2 is not None:
                k2 = self.prepExtraDims(plot.var2.var)
                args.append(plot.var2.var(**k2))
                cmd += "%s(**%s), " % (args[-1].id, str(k2))
            #args.append(plot.template)
            cgm = self.get_graphics_method(plot.plot_type,
                                           plot.graphics_method_name)
#            cgm.setProvenanceHandler( plot.processParameterUpdate )
            if plot.graphics_method_name != 'default':
                #cgm.list()
                for k in plot.gm_attributes:
                    if hasattr(plot, k):
                        if k in ['legend']:
                            setattr(cgm, k, eval(getattr(plot, k)))
                        else:
                            if getattr(plot, k) != getattr(cgm, k):
                                try:
                                    setattr(cgm, k, eval(getattr(plot, k)))
                                except:
                                    setattr(cgm, k, getattr(plot, k))

            kwargs = plot.kwargs
            file_path = None
            for fname in [plot.var.file, plot.var.filename]:
                if fname and (os.path.isfile(fname) or
                              fname.startswith('http://')):
                    file_path = fname
                    break
            if not file_path and plot.var.url:
                file_path = plot.var.url
            if file_path:
                kwargs['cdmsfile'] = file_path
            # record commands
            cmd += " '%s', '%s'" % (plot.template, cgm.name)
            for k in kwargs:
                cmd += ", %s=%s" % (k, repr(kwargs[k]))
            cmd += ")"
            #from vistrails.gui.application import get_vistrails_application
            #_app = get_vistrails_application()
            #conf = get_vistrails_configuration()
            #interactive = conf.check('interactiveMode')
            #if interactive:
            #    _app.uvcdatWindow.record(cmd)

            # apply colormap
            if plot.colorMap is not None:
                if plot.colorMap.colorMapName is not None:
                    self.canvas.setcolormap(str(plot.colorMap.colorMapName))

                if plot.colorMap.colorCells is not None:
                    for (n, r, g, b) in plot.colorMap.colorCells:
                        self.canvas.canvas.setcolorcell(n, r, g, b)
                    # see vcs.Canvas.setcolorcell
                    # pass down self and mode to _vcs module
                    self.canvas.canvas.updateVCSsegments(self.canvas.mode)
                    # update the canvas by processing all the X events
                    self.canvas.flush()

#            try:
            self.canvas.plot(cgm, *args, **kwargs)
#             except Exception, e:
#                 spreadsheetWindow.setUpdatesEnabled(True)
#                 raise e
        #self.canvas.setAnimationStepper( QtAnimationStepper )
        spreadsheetWindow.setUpdatesEnabled(True)
        self.update()

        # make sure reparented windows stay invisible
        #for windowId in reparentedVCSWindows:
        #    reparentedVCSWindows[windowId].setVisible(False)

    def get_graphics_method(self, plotType, gmName):
        method_name = "get" + str(plotType).lower()
        return getattr(self.canvas, method_name)(gmName)

    def deleteLater(self):
        """ deleteLater() -> None
        Make sure to free render window resource when
        deallocating. Overriding PyQt deleteLater to free up
        resources
        """
        # we need to re-parent self.window or it will be deleted together with
        # this widget. We'll put it on the mainwindow
        #_app = get_vistrails_application()
        #if self.window is not None:
        #    if hasattr(_app, 'uvcdatWindow'):
        #        self.window.setParent(_app.uvcdatWindow)
        #    else: #uvcdatWindow is not setup when running in batch mode
        #        self.window.setParent(QtGui.QApplication.activeWindow())
        #    self.window.setVisible(False)
        #    reparentedVCSWindows[self.windowId] = self.window

        self.canvas = None
        #self.window = None

        QCellWidget.deleteLater(self)

    def dumpToFile(self, filename):
        """ dumpToFile(filename: str, dump_as_pdf: bool) -> None
        Dumps itself as an image to a file, calling grabWindowPixmap """
        _, ext = os.path.splitext(filename)
        if ext.upper() == '.PDF':
            self.canvas.pdf(filename)  #, width=11.5)
        elif ext.upper() == ".PNG":
            self.canvas.png(filename)  #, width=11.5)
        elif ext.upper() == ".SVG":
            self.canvas.svg(filename)  #, width=11.5)
        elif ext.upper() == ".GIF":
            self.canvas.gif(filename)  #, width=11.5)
        elif ext.upper() == ".PS":
            self.canvas.postscript(filename)  #, width=11.5)

    def saveToPNG(self, filename):
        """ saveToPNG(filename: str) -> bool
        Save the current widget contents to an image file

        """

        self.canvas.png(filename)

    def saveToPDF(self, filename):
        """ saveToPDF(filename: str) -> bool
        Save the current widget contents to a pdf file

        """
        self.canvas.pdf(filename)  #, width=11.5)


_modules = [VariableSource,
            CDMSVariable, CDMSPlot, CDMS2DPlot, CDMS3DPlot, CDMSCell,
            CDMSTDMarker, CDMSVariableOperation, CDMSUnaryVariableOperation,
            CDMSBinaryVariableOperation, CDMSNaryVariableOperation,
            CDMSColorMap, CDMSGrowerOperation]


def get_input_ports(plot_type):
    if plot_type == "Boxfill":
        ports = [('boxfill_type', 'basic:String', True),
                 ('color_1', 'basic:Integer', True),
                 ('color_2', 'basic:Integer', True),
                 ('levels', 'basic:List', True),
                 ('ext_1', 'basic:Boolean', True),
                 ('ext_2', 'basic:Boolean', True),
                 ('fillareacolors', 'basic:List', True),
                 ('fillareaindices', 'basic:List', True),
                 ('fillareastyle', 'basic:String', True),
                 ('legend', 'basic:String', True),
                 ('level_1', 'basic:Float', True),
                 ('level_2', 'basic:Float', True),
                 ('missing', 'basic:Integer', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True)]
    elif (plot_type == "3D_Scalar") or (plot_type == "3D_Dual_Scalar"):
        from DV3D.ConfigurationFunctions import ConfigManager
        from DV3D.DV3DPlot import PlotButtonNames
        cfgManager = ConfigManager()
        parameterList = cfgManager.getParameterList(extras=(PlotButtonNames +
                                                            ['axes']))
        ports = [(pname, 'basic:String', True) for pname in parameterList]

    elif plot_type == "3D_Vector":
        from DV3D.ConfigurationFunctions import ConfigManager
        from DV3D.DV3DPlot import PlotButtonNames
        cfgManager = ConfigManager()
        parameterList = cfgManager.getParameterList(extras=(PlotButtonNames +
                                                            ['axes']))
        ports = [(pname, 'basic:String', True) for pname in parameterList]

    elif plot_type == "Isofill":
        ports = [('levels', 'basic:List', True),
                 ('ext_1', 'basic:Boolean', True),
                 ('ext_2', 'basic:Boolean', True),
                 ('fillareacolors', 'basic:List', True),
                 ('fillareaindices', 'basic:List', True),
                 ('fillareastyle', 'basic:String', True),
                 ('legend', 'basic:String', True),
                 ('missing', 'basic:Integer', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True)]
    elif plot_type == "Isoline":
        ports = [('label', 'basic:String', True),
                 ('levels', 'basic:List', True),
                 ('ext_1', 'basic:Boolean', True),
                 ('ext_2', 'basic:Boolean', True),
                 ('level', 'basic:List', True),
                 ('line', 'basic:List', True),
                 ('linecolors', 'basic:List', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True),
                 ('linewidths', 'basic:List', True),
                 ('text', 'basic:List', True),
                 ('textcolors', 'basic:List', True),
                 ('clockwise', 'basic:List', True),
                 ('scale', 'basic:List', True),
                 ('angle', 'basic:List', True),
                 ('spacing', 'basic:List', True)]
    elif plot_type == "Meshfill":
        ports = [('levels', 'basic:List', True),
                 ('ext_1', 'basic:Boolean', True),
                 ('ext_2', 'basic:Boolean', True),
                 ('fillareacolors', 'basic:List', True),
                 ('fillareaindices', 'basic:List', True),
                 ('fillareastyle', 'basic:String', True),
                 ('legend', 'basic:String', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True),
                 ('missing', 'basic:Integer', True),
                 ('mesh', 'basic:String', True),
                 ('wrap', 'basic:List', True)]
    elif plot_type == "Scatter":
        ports = [('markercolor', 'basic:Integer', True),
                 ('marker', 'basic:String', True),
                 ('markersize', 'basic:Integer', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True)]
    elif plot_type == "Vector":
        ports = [('scale', 'basic:Float', True),
                 ('alignment', 'basic:String', True),
                 ('type', 'basic:String', True),
                 ('reference', 'basic:Float', True),
                 ('linecolor', 'basic:Integer', True),
                 ('line', 'basic:String', True),
                 ('linewidth', 'basic:Integer', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True)]
    elif plot_type == "XvsY":
        ports = [('linecolor', 'basic:Integer', True),
                 ('line', 'basic:String', True),
                 ('linewidth', 'basic:Integer', True),
                 ('markercolor', 'basic:Integer', True),
                 ('marker', 'basic:String', True),
                 ('markersize', 'basic:Integer', True),
                 ('xaxisconvert', 'basic:String', True),
                 ('yaxisconvert', 'basic:String', True)]
    elif plot_type == "Xyvsy":
        ports = [('linecolor', 'basic:Integer', True),
                 ('line', 'basic:String', True),
                 ('linewidth', 'basic:Integer', True),
                 ('markercolor', 'basic:Integer', True),
                 ('marker', 'basic:String', True),
                 ('markersize', 'basic:Integer', True),
                 ('yaxisconvert', 'basic:String', True)]
    elif plot_type == "Yxvsx":
        ports = [('linecolor', 'basic:Integer', True),
                 ('line', 'basic:String', True),
                 ('linewidth', 'basic:Integer', True),
                 ('markercolor', 'basic:Integer', True),
                 ('marker', 'basic:String', True),
                 ('markersize', 'basic:Integer', True),
                 ('xaxisconvert', 'basic:String', True)]
    elif plot_type == "Taylordiagram":
        ports = [('detail', 'basic:Integer', True),
                 ('max', 'basic:Integer', True),
                 ('quadrans', 'basic:Integer', True),
                 ('skillColor', 'basic:String', True),
                 ('skillValues', 'basic:List', True),
                 ('skillDrawLabels', 'basic:String', True),
                 ('skillCoefficient', 'basic:List', True),
                 ('referencevalue', 'basic:Float', True),
                 ('arrowlength', 'basic:Float', True),
                 ('arrowangle', 'basic:Float', True),
                 ('arrowbase', 'basic:Float', True),
                 ('cmtics1', 'basic:String', True),
                 ('cticlabels1', 'basic:String', True),
                 ('Marker', 'basic:String', True)]
    else:
        ports = []

    gms = [('graphicsMethodName', 'basic:String',
            {'entry_types': ['enum'],
             'values': [repr(original_gm_attributes[plot_type].keys())]})]

    return gms + ports


for superklass, typeslist in (
        (CDMS2DPlot, ('Boxfill', 'Isofill', 'Isoline', 'Meshfill',
                      'Scatter', 'Taylordiagram', 'Vector',
                      'XvsY', 'Xyvsy', 'Yxvsx')),
        (CDMS3DPlot, ('3D_Scalar', '3D_Dual_Scalar', '3D_Vector'))):
    for plot_type in typeslist:
        klass = type('CDMS' + plot_type, (superklass,),
                     {'plot_type': plot_type,
                      '_input_ports': get_input_ports(plot_type),
                      'gm_attributes': get_gm_attributes(plot_type)})

        _modules.append(klass)


try:
    import dat.packages
except ImportError:
    pass  # DAT is not available
else:
    from .dat_integration import *