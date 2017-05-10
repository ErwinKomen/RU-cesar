/**
 * Copyright (c) 2017 Radboud University Nijmegen.
 * All rights reserved.
 *
 * @author Erwin R. Komen
 */

/*globals jQuery, crpstudio, Crpstudio, alert: false, */
var crpstudio = (function ($, crpstudio) {
  "use strict";
  crpstudio.tree = (function ($, config) {
    // Local variables within crpstudio.tree
    var marginLeft = 10,      // Margin of whole figure
        wordSpacing = 12,     // Space between nodes
        branchHeight = 70,    // Height between branches
        shadowDepth = 5,      // How thick the shadow is
        bDebug = false,       // Debugging set or not
        level = 0,            // Recursion level of vertical draw tree
        graphAbstract = {},   // Representation of the total
        width = 1025,         // Initial canvas width
        height = 631,         // Initial canvas height
        errDiv = null,        // Where to show errors
        loc_arLeaf = [],      // Storage of pointers to the LEAFs of the tree
        loc_iTreeId = 0,      // Available ID's for tree
        loc_iShadow = 3,      // 
        loc_iMargin = 5,      // margin of box around tree image
        loc_iWidth = 0.5,     // Stroke-width in 
        loc_iMaxLevel = 0,    // Maximum hierarchical level of this tree
        loc_iDistVert = 60,   // Vertical distance between tree nodes
        loc_iDistHor = 5,     // Minimal distance between end nodes
        root = null;          // Root of the tree (DOM position)

    // Methods that are local to [crpstudio.dbase]
    var private_methods = {
      /**
       * showError
       *     Show the error at the indicated place
       */
      showError: function (sFunction, ex) {
        var sMsg = "Error in " + sFunction + ": " + ex.message;
        if (errDiv !== undefined) $(errDiv).html(sMsg);
      },
      initSvg: function () {
        var lHtml = [];

        try {
          // Create an <svg> element
          lHtml.push("<svg width='1047px' height='542px' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>");
          lHtml.push("<defs>");
          for (i = 0; i < arCol.length; i++) {
            lHtml.push("<linearGradient id='" + arCol[i] + "_gradient'><stop offset='5%' stop-color='" + arCol[i] + "' />");
            lHtml.push("<stop offset='95%' stop-color='whitesmoke' /></linearGradient>");
          }
          lHtml.push("</defs>");
          // Finish the tree
          lHtml.push("</svg>");
          return lHtml.join("\n");
        } catch (ex) {
          private_methods.showError("initSvg", ex);
          return "";
        }
      },
      /**
       * centerRoot
       *    Set the [root] in the center of [width] and [height]
       * 
       * @param {type} el
       * @returns {void}
       */
      centerRoot: function (el) {
        try {
          // Validate: exist and must be <g> with class "lithium-root"
          if (el === undefined) return false;
          if (!$(el).is(".lithium-tree")) return false;
          var oRect = {
            x: Math.ceil(width / 2),
            y: Math.ceil(height / 2),
            width: parseInt($(el).attr("width"), 10),
            height: parseInt($(el).attr("height"), 10)
          };
          private_methods.setLocation(el, oRect);
        } catch (ex) {
          private_methods.showError("centerRoot", ex);
        }
      },
      initTreeId: function () { loc_iTreeId = 0; },
      getTreeId: function () { loc_iTreeId += 1; return loc_iTreeId;},
      getText: function (el) {
        try {
          // Validate
          if (el === undefined) return "";
          if (!$(el).is(".lithium-tree")) return "";
          return $(el).children(".lithium-node").children("text").first().text();
        } catch (ex) {
          private_methods.showError("getText", ex);
          return null;
        }
      },
      classAdd: function (el, sClass) {
        var arClass = [], idx, sList;

        try {
          sList = $(el).attr("class");
          if (sList !== undefined && sList !== "") {
            arClass = sList.split(" ");
          }
          idx = arClass.indexOf(sClass);
          if (idx < 0) { arClass.push(sClass); }
          $(el).attr("class", arClass.join(" "));
        } catch (ex) {
          private_methods.showError("classAdd", ex);
        }
      },
      classRemove: function (el, sClass) {
        var arClass = [], idx, sList;

        try {
          sList = $(el).attr("class");
          if (sList !== undefined && sList !== "") {
            arClass = sList.split(" ");
          }
          idx = arClass.indexOf(sClass);
          if (idx >= 0) { arClass.splice(idx, 1); }
          $(el).attr("class", arClass.join(" "));
        } catch (ex) {
          private_methods.showError("classRemove", ex);
        }
      },
      /**
       * setLocation
       *    If this is a <g> element from 'lithium-tree', then
       *    set the x,y,width,height attributes according to oRect
       * 
       * @param {type} el
       * @param {type} oRect
       * @returns {Boolean}
       */
      setLocation: function (el, oRect) {
        try {
          // Validate: exist and must be <g> with class "lithium-tree"
          if (el === undefined) return false;
          if (!$(el).is(".lithium-tree")) return false;
          $(el).attr("x", oRect['x']);
          $(el).attr("y", oRect['y']);
          // Optionally set width and height
          if (oRect.hasOwnProperty("width")) { $(el).attr("width", oRect['width']); }
          if (oRect.hasOwnProperty("height")) { $(el).attr("height", oRect['height']); }
          // Debugging: immediately apply this location
          private_methods.applyOneLocation(el);
          return true;
        } catch (ex) {
          private_methods.showError("setLocation", ex);
          return false;
        }
      },
      /**
       * getLocation
       *    If this is a <g> element from 'lithium-root', then
       *    set the x,y,width,height attributes according to oRect
       *        
       * @param {type} el
       * @returns {crpstudio_tree_L9.crpstudio_tree_L11.private_methods.getLocation.oRect}
       */
      getLocation: function (el) {
        var oRect = {};

        try {
          // Validate: exist and must be <g> with class "lithium-root"
          if (el === undefined) return oRect;
          if (!$(el).is(".lithium-tree")) return oRect;
          oRect['x'] = parseInt($(el).attr("x"), 10);
          oRect['y'] = parseInt($(el).attr("y"), 10);
          oRect['width'] = parseInt($(el).attr("width"), 10);
          oRect['height'] = parseInt($(el).attr("height"), 10);
          oRect['expanded'] = private_methods.isVisible(el);
          return oRect;
        } catch (ex) {
          private_methods.showError("getLocation", ex);
          return null;
        }
      },
      /**
       * applyLocations
       *    Visit each .lithium-tree element and apply the position changes
       *    to its <rect>, <text> and <line> elements
       * 
       * @param {type} el
       * @param {string} sType
       * @returns {boolean}
       */
      applyLocations: function (el, sType) {
        var gParent, sPath;

        try {
          // Validate
          if (el === undefined) return false;
          switch (sType) {
            case "loc":
              // Visit all lithium-tree elements
              $(el).find(".lithium-tree").each(function () {
                private_methods.applyOneLocation(this);
              });
              break;
            case "conn":
              // Visit all lithium-tree elements
              $(el).find(".lithium-tree").each(function () {
                // Re-create the [conn] to go from me to my parent
                gParent = $(this).parent();
                if ($(gParent).is(".lithium-tree")) {
                  sPath = private_methods.svgConn(this, gParent);
                  $(this).children(".lithium-conn").first().html(sPath);
                }
              });
              break;
          }

          // Return positively
          return true;
        } catch (ex) {
          private_methods.showError("applyLocations", ex);
          return false;
        }
      },
      /**
       * applyOneLocation
       *    Apply changes to this one location
       * 
       * @param {type} gThis
       * @returns {undefined}
       */
      applyOneLocation: function (gThis) {
        try {
          // Validate
          if (gThis === undefined) return false;
          if (!$(gThis).is(".lithium-tree")) return false;
          // Get my main components
          var node = $(gThis).children(".lithium-node").first();
          // The [node] contains: [rect], [shadow] and [text]
          var mainRect = $(node).children("rect").first();
          var shadowRect = $(node).children(".lithium-shadow").children("rect").first();
          var mainText = $(node).children("text").first();
          // Calculate the shift
          var shift_x = parseInt($(gThis).attr("x"), 10) - parseInt($(mainRect).attr("x"), 10);
          var shift_y = parseInt($(gThis).attr("y"), 10) - parseInt($(mainRect).attr("y"), 10);
          var new_w = parseInt($(gThis).attr("width"), 10);
          var new_h = parseInt($(gThis).attr("height"), 10);
          // Apply the shift to the rect-elements
          private_methods.applyRectShiftSize(mainRect, shift_x, shift_y, new_w, new_h);
          private_methods.applyRectShiftSize(shadowRect, shift_x, shift_y, new_w, new_h);
          // Apply the rect-like shift to the <text> element
          //   (but do not change its size)
          private_methods.applyRectShiftSize(mainText, shift_x, shift_y, -1, -1);
          // Do we have a toggle?
          var toggle = $(gThis).children(".lithium-toggle");
          if ($(toggle).length > 0) {
            // Treat the [toggle]
            var toggleRect = $(toggle).children("rect").first();
            var toggleLines = $(toggle).children("line");
            // Calculate the toggle position
            var oToggle = private_methods.getRectSize(toggleRect);
            oToggle['x'] = parseInt($(mainRect).attr("x"), 10) +
                 Math.ceil((parseInt($(mainRect).attr("width"), 10) -
                                     oToggle['width']) / 2);
            oToggle['y'] = Math.ceil(parseInt($(mainRect).attr("y"), 10) + new_h);
            // Now clear the entire toggle contents
            $(toggle).empty();
            // Start building up again: add the correct rect
            var sRect = private_methods.svgRect(oToggle);

            // The visibility of the vertical bar depends on whether one or more children are invisible
            var bPlus = private_methods.isVisible($(gThis).children(".lithium-tree").first());

            // Create new content
            var sLines = private_methods.crossInRect(oToggle, bPlus);
            // Add this content
            $(toggle).html(sRect + sLines);
          }
          // Connections: special case TODO: adapt
          var connPart = $(gThis).children(".lithium-conn");
          if ($(connPart).length > 0) $(connPart).empty();
          return true;
        } catch (ex) {
          private_methods.showError("applyOneLocation", ex);
          return false;
        }
      },
      /**
       * svgConn
       *    Create the SVG text of a path from src to dst
       *    where these are <g> elements of class 'lithium-tree'
       * 
       * @param {type} gSrc
       * @param {type} gDst
       * @param {type} oParams
       * @returns {undefined}
       */
      svgConn: function (gSrc, gDst, oParams) {
        try {
          // Validate
          if (!$(gSrc).is(".lithium-tree") || !$(gSrc).is(".lithium-tree")) return "";
          // Get the start and end rectangles
          var oSrc = private_methods.getRectSize(gSrc, ".lithium-tree");
          var oDst = private_methods.getRectSize(gDst, ".lithium-tree");
          if (oSrc === null || oDst === null) return "";
          // Set default values
          var sStroke = "black";
          var sStrokeWidth = "0.5";
          if (oParams !== undefined) {
            if (oParams.hasOwnProperty("stroke")) sStroke = oParams["stroke"];
            if (oParams.hasOwnProperty("stroke-width")) sStrokeWidth = oParams["stroke-width"];
          }
          // Calculate three points
          var iHalfWsrc = Math.ceil(oSrc['width'] / 2);
          var iHalfWdst = Math.ceil(oDst['width'] / 2);
          var p1 = {
            x: oSrc['x'] + iHalfWsrc,
            y: oSrc['y']
          };
          var p2 = {
            x: p1['x'],
            y: Math.ceil((oDst['y'] + oSrc['y'] + oDst['height']) / 2)
          };
          var p3 = {
            x: oDst['x'] + iHalfWdst,
            y: p2['y']
          };
          var p4 = {
            x: p3['x'],
            y: oDst['y'] + oDst['height']
          };
          // Small 1-pixel rectifications
          if (Math.abs(p2['x'] - p3['x']) === 1) {
            // Adjust p1 and p2
            p1['x'] = p3['x'];
            p2['x'] = p3['x'];
          }
          // Start building the correct path
          var sHtml = [];
          // Start: supply starting point [p1]
          sHtml.push("<path d='M" + p1['x'] + " " + p1['y']);
          // vertical line from p1 to p2
          sHtml.push("L" + p2['x'] + " " + p2['y']);
          // horizontal line from p2 - p3
          sHtml.push("L" + p3['x'] + " " + p3['y']);
          // vertical line from p3 - p4
          sHtml.push("L" + p4['x'] + " " + p4['y']);
          // Finish the path
          sHtml.push("'"); // sHtml.push("Z'");
          // Supply the other parameters
          sHtml.push("stroke='" + sStroke + "'");
          sHtml.push("stroke-width='" + sStrokeWidth + "'");
          sHtml.push("fill='none' />");
          // Return what we have made
          return sHtml.join(" ");
        } catch (ex) {
          private_methods.showError("svgConn", ex);
          return null;
        }

      },
      /**
       * svgRect
       *    Construct a rectangle according to the parameters in [oRect]
       * 
       * @param {type} oRect
       * @returns {undefined}
       */
      svgRect: function (oRect) {
        try {
          // Validate
          if (!oRect.hasOwnProperty("x") || !oRect.hasOwnProperty("y") ||
              !oRect.hasOwnProperty("width") || !oRect.hasOwnProperty("height")) return "[RECT-ERROR]";
          // Add default arguments if  needed
          if (!oRect.hasOwnProperty("stroke")) oRect['stroke'] = "black";
          if (!oRect.hasOwnProperty("stroke-width")) oRect['stroke-width'] = "0.5";
          if (!oRect.hasOwnProperty("fill")) oRect['fill'] = "white";
          // Now create the svg stuff
          var sBack = "<rect x='" + oRect['x'] +
                          "' y='" + oRect['y'] +
                          "' width='" + oRect['width'] +
                          "' height='" + oRect['height'] +
                          "' fill='" + oRect['fill'] +
                          "' stroke='" + oRect['stroke'] +
                          "' stroke-width='" + oRect['stroke-width'] + "' />";
          // Return what we made
          return sBack;
        } catch (ex) {
          private_methods.showError("svgRect", ex);
          return null;
        }
      },
      rectShadow : function(options) {
        var x, y, w, h;

        try {
          x = options['x'];
          y = options['y'];
          w = options['w'];
          h = options['h'];

          return private_method.svgRect({
            x: x + loc_iShadow, y: y + loc_iShadow, width: w, height: h, rx: loc_iShadow, ry: loc_iShadow,
            fill: "gainsboro", stroke: "gainsboro", 'stroke-width': loc_iWidth
          });
        } catch (ex) {
          private_methods.showError("rectShadow", ex);
          return "";
        }
      },
      rectNode: function (options) {
        var x, y, w, h,   // Coordinates
            sColor;       // Color

        try {
          // Get the coordinates
          x = options['x'];
          y = options['y'];
          w = options['w'];
          h = options['h'];
          // Determine the color
          switch (options['type']) {
            case "end": sColor = "url(#ivory_gradient)"; break;
            case "node": sColor = "url(#steelblue_gradient)"; break;
            case "sel": sColor = "url(#darkgoldenrod_gradient)"; break;
          }

          return private_method.svgRect({
            x: x , y: y , width: w, height: h, rx: loc_iShadow, ry: loc_iShadow,
            fill: sColor, stroke: "black", 'stroke-width': loc_iWidth
          });
        } catch (ex) {
          private_methods.showError("rectNode", ex);
          return "";
        }
      },
      /**
       * crossInRect
       *    Make the SVG (string) for a vertical and horizontal bar within [oRect]
       * 
       * @param {type} oRect
       * @param {type} bPlus
       * @returns {undefined}
       */
      crossInRect: function (oRect, bPlus) {
        var lHtml = [];

        try {
          // Horizontal line: not hidden
          lHtml.push(private_methods.svgLine(oRect['x'] + 1,
              oRect['y'] + Math.ceil(oRect['height'] / 2),
              oRect['x'] + oRect['width'] - 1,
              oRect['y'] + Math.ceil(oRect['height'] / 2),
              false));
          // Vertical line: hidden (initially)
          lHtml.push(private_methods.svgLine(
              oRect['x'] + Math.ceil(oRect['width'] / 2),
              oRect['y'] + 1,
              oRect['x'] + Math.ceil(oRect['width'] / 2),
              oRect['y'] + oRect['height'] - 1,
              bPlus));
          // Return the combination
          return lHtml.join("\n");
        } catch (ex) {
          private_methods.showError("crossInRect", ex);
          return null;
        }
      },
      /**
       * svgLine
       *    Make the SVG code for a line from [x1,y1] to [x2,y2]
       *    Add class "hidden" if [bHidden] is true
       * 
       * @param {type} x1
       * @param {type} y1
       * @param {type} x2
       * @param {type} y2
       * @param {type} bHidden
       * @returns {undefined}
       */
      svgLine: function (x1, y1, x2, y2, bHidden) {
        try {
          var sLine = "<line x1='" + x1 +
                      "' y1='" + y1 + "' x2='" + x2 +
                      "' y2='" + y2 + "' stroke='black' stroke-width='0.5' />";
          if (bHidden) {
            sLine = "<g class='lithium-vbar hidden'>" +
                    sLine + "</g>";
          }
          return sLine;
        } catch (ex) {
          private_methods.showError("svgLine", ex);
          return "";
        }
      },
      applyRectShiftSize: function (el, shift_x, shift_y, new_w, new_h) {
        try {
          // Apply the shift to the rect-elements
          $(el).attr("x", parseInt($(el).attr("x"), 10) + shift_x);
          $(el).attr("y", parseInt($(el).attr("y"), 10) + shift_y);
          if (new_w > 0) parseInt($(el).attr("width", new_w), 10);
          if (new_h > 0) parseInt($(el).attr("height", new_h), 10);
          return true;
        } catch (ex) {
          private_methods.showError("applyRectShiftSize", ex);
          return false;
        }
      },
      applyLineShift: function (el, shift_x, shift_y) {
        try {
          // Apply the shift to the rect-elements
          $(el).attr("x1", parseInt($(el).attr("x1"), 10) + shift_x);
          $(el).attr("y1", parseInt($(el).attr("y1"), 10) + shift_y);
          $(el).attr("x2", parseInt($(el).attr("x2"), 10) + shift_x);
          $(el).attr("y2", parseInt($(el).attr("y2"), 10) + shift_y);
        } catch (ex) {
          private_methods.showError("applyLineShift", ex);
        }
      },
      /**
       * nodeToSvg
       *    Convert one node to an svg <g> element (recursively)
       *
       *  @param {object} oNode
       *  @param {DOM}    dParent - Is this a root node or not
       *  @return {DOM}
       */
      nodeToSvg : function(oNode, dParent) {
        var lHtml = [],   // Storage of the HTML produced
            lChild = [],  // Storage of the children in HTML
            i,            // Counter
            x = 0,        // Coordinate
            y = 0,        // Coordinate
            w = 22,       // Width
            h = 22,       // Height
            sClass = "",
            sText = "",   // Text for this node
            sPos = "",    // POS for this node
            sTree = "",   // Text of <g> 'tree'   part
            sNode = "",   // Text of <g> 'node'   part
            sToggle = "", // Text of <g> 'toggle' part
            sConn = "",   // Text of <g> 'conn'   part
            svgRect = "",
            svgText = "",
            dNode = null, // Current SVG DOM master element
            dLeaf = null, // SVG DOM leaf element
            dPrev = null, // Preceding DOM leaf element
            dPrevP = null,// Parent of dPrev
            oPos = {},    // General purpose position object
            oPosN = {},   // Position of the node
            sType = "",   // The type of situation we are in
            oChild = {};  // One child of [oNode]

        try {
          // Validate
          if (oNode === undefined) return "";
          if (!oNode.hasOwnProperty("p") || !oNode.hasOwnProperty("level") || !oNode.hasOwnProperty("id")) return "";
          // Get the POS of the node
          sPos = oNode['pos'];
          // Create an svg <g> element that contains its ID and CLASS
          sTree = private_methods.getLithiumNode({ el: oNode, type: "node" });
          dNode = $(dParent).append(sTree);
          // Fit the text in the node (and this also sets the 'width' and 'height' of the <g> element)
          private_methods.fitRectangle(dNode);
          // Set the node's w/h
          oPosN['width'] = $(dNode).width;
          oPosN['height'] = $(dNode).height;
          oPosN['y'] = oNode['level'] * loc_iDistVert + loc_iMargin;
          // What is the situation
          sType = (oNode.hasOwnProperty("child")) ? "node" : "terminal";
          switch (sType) {
            case "terminal":
              // THis is an end-node: it must contain text
              if (!oNode.hasOwnProperty("txt")) return "";
              // Create an SVG 'lithium-node'
              sNode = private_methods.getLithiumNode({ el: oNode, type: 'terminal' });
              // Add this leaf node under [dNode]
              dLeaf = $(dNode).append(sNode);
              // Fit the text in the leaf
              private_methods.fitRectangle(dLeaf);
              // The w,h are needed for 'setLocation'
              oPos['width'] = $(dLeaf).width;
              oPos['height'] = $(dLeaf).height;
              // Determine the x,y for the leaf
              if (loc_arLeaf.length === 0) {
                // This is the first terminal
                x = loc_iMargin;
                // TODO: differentiate between two types of end-nodes: Vern+Punct versus Zero+Star
                oPos['y'] = (loc_iMaxLevel + 1) * loc_iDistVert + loc_iMargin;
              } else {
                // Get the first preceding tree/leaf combination
                dPrev = loc_arLeaf.last(); dPrevP = $(dPrev).parent();
                // Get the rightmost point of this leaf or its parent node
                x = Math.max($(dPrev).x + $(dPrev).width, $(dPrevP).x + $(dPrevP).width) + loc_iDistHor;
                // The vertical position of [dLeaf] is determined by the level
                oPos['y'] = (oNode['level'] + 1) * loc_iDistVert + loc_iMargin;
              }
              // Set the x,y of [dLeaf] and its parent [dNode]
              if ($(dLeaf).width > $(dNode).width) {
                // First dLeaf
                oPos['x'] = x;
                private_methods.setLocation(dLeaf, oPos);
                // Adapt x position of the parent [dNode]
                oPosN['x'] = oPos['x'] + $(dLeaf).width / 2 - $(dNode).width / 2;
                // Set the location of the node
                private_methods.setLocation(dNode, oPosN);
              } else {
                // First set the location of the dNode
                oPosN['x'] = x;
                private_methods.setLocation(dNode, oPosN);
                // Then determine the location of the leaf
                oPos['x'] = oPosN['x'] + $(dNode).width / 2 - $(dLeaf).width / 2;
                private_methods.setLocation(dLeaf, oPos);
              }
              

              // Store the node in the global variable
              loc_arLeaf.push(dLeaf);
              break;
            default:  // Normal nodes
              // Determine x,y
              break;
          }

          // REturn the node that has been created
          return dNode;
        } catch (ex) {
          // Show error message
          private_methods.showError("nodeToSvg", ex);
          // Return empty string
          return null;
        }
      },
      /**
       *  getLithiumNode
       *    Create a class='lithium-node' item
       *
       *  @param {object} options
       *  @return {string}
       */
      getLithiumNode: function (options) {
        var lHtml = [],
            sText = "",
            el,
            x = 0,
            y = 0,
            w = 10,
            h=10,
            sType;

        try {
          // Get obligatory parameters
          sType = options['type'];
          el = options['el'];
          // Action depends on type
          switch (sType) {
            case "terminal":  // This is a terminal node
              // Get the text of the node
              sText = el['txt'];
              // Add a 'tree_leaf'  element
              lHtml.push(private_methods.getGstart({ type: "tree_leaf", el: el, x: x, y: y, width: w, height: h }));
              if (el.parent !== null) {
                // Add a <g> 'lithium-conn' part: connection with the parent
                lHtml.push(private_methods.getGstart({ type: "conn_leaf", el: el }));
                // Finish the 'lithium-conn' part
                lHtml.push("</g>");
              }

              // Add a <g> 'lithium-node' part + its shadow
              lHtml.push(private_methods.getGstart({ type: "node_leaf", el: el }));
              lHtml.push(private_methods.getGstart({ type: "shadow", el: el }));
              // Add a <rect> element to realise the shadow
              lHtml.push(private_methods.rectShadow({ x: x, y: y, w: w, h: h }));
              // Finish the shadow
              lHtml.push("</g>");
              // Add an end-node rect
              lHtml.push(private_methods.rectNode({ x: x, y: y, w: w, h: h, type: "end" }));
              // Add a <text> node
              lhtml.push(private_methods.textNode({ x: x, y: x, t: sText }));
              // Finish the 'node_leaf'
              lHtml.push("</g>");
              // Finish the 'tree_leaf'
              lHtml.push("</g>");
              break;
            default:          // THis is a non-terminal node
              // The text of the node is the POS
              sText = el['pos'];
              // Add a 'tree'  element
              lHtml.push(private_methods.getGstart({ type: "tree", el: el, x: x, y: y, width: w, height: h }));
              if (el.parent !== null) {
                // Add a <g> 'lithium-conn' part: connection with the parent
                lHtml.push(private_methods.getGstart({ type: "conn", el: el }));
                // Finish the 'lithium-conn' part
                lHtml.push("</g>");
              }

              // Add a <g> 'lithium-node' part + its shadow
              lHtml.push(private_methods.getGstart({ type: "node", el: el }));
              lHtml.push(private_methods.getGstart({ type: "shadow", el: el }));
              // Add a <rect> element to realise the shadow
              lHtml.push(private_methods.rectShadow({ x: x, y: y, w: w, h: h }));
              // Finish the shadow
              lHtml.push("</g>");
              // Add an end-node rect
              lHtml.push(private_methods.rectNode({ x: x, y: y, w: w, h: h, type: "node" }));
              // Add a <text> node
              lhtml.push(private_methods.textNode({ x: x, y: x, t: sText }));
              // Finish the 'node_leaf'
              lHtml.push("</g>");
              // Finish the 'tree_leaf'
              lHtml.push("</g>");
              break;
          }


          // REturn what we found
          return lHtml.join("\n");
        } catch (ex) {
          // Show error message
          private_methods.showError("getLithiumNode", ex);
          // Return empty string
          return "";
        }
      },
      /**
       *  setParentAndId
       *    Add a 'parent' link to each node in o recursively
       *    Add a unique numerical 'id' to each node in o
       *
       *  @param {object} o   - myself
       *  @param {object} p   - my parent
       *  @param {int} iLevel - deepness level
       *  @return {void}
       */
      setParentAndId: function (o, p, iLevel) {
        try {
          // CHeck for level
          if (p===null) loc_iMaxLevel = 0;
          // Check for ID
          if (!o.hasOwnProperty("id")) { o['id'] = private_methods.getTreeId(); }
          // Check for level
          if (!o.hasOwnProperty("level")) { o['level'] = iLevel; }
          // CHeck for parent
          if (!o.hasOwnProperty("parent")) { o['parent'] = p;}
          // Check for children
          if (o.hasOwnProperty('child') && o.child != null) {
            // Go one level down
            iLevel += 1;
            if (iLevel > loc_iMaxLevel) {loc_iMaxLevel = iLevel;}
            // Treat all children
            for (n in o.child) {
              // Treat this particular child
              private_methods.setParentAndId(o.nodes[n], o, iLevel);
            }
            // Go one level up again
            iLevel -= 1;
          }
        } catch (ex) {
          // Show error message
          private_methods.showError("setParent", ex);
          // Return empty string
          return "";
        }
      },
      /**
       * getG
       *    Create a <g> element with the specified options
       *
       * @param {object} options: 
       *                      type (obligatory): tree, conn, node, toggle
       *                      el   (obligatory): the current element
       *                      root (obligatory)
       *                      x, y, width, height (optional)
       *                          
       * @return {string}
       */
      getGstart: function (options) {
        var lHtml = [],
            oThis = {},     // Current object
            oParent = {},   // Possibly the parent node
            sClass = "";

        try {
          lHtml.push("<g");
          // Obligatory: @type, @el
          if (!options.hasOwnProperty("type") || !options.hasOwnProperty("el")) { return ""; }
          // Get the current object
          oThis = options['el'];
          // Add the @id
          switch (options['type']) {
            case "conn":  // Connection from this to parent
              oParent = oThis['parent'];
              lHtml.push("id='" + options['type'] + "_" + oThis['id'] + "_" + oParent['id'] + "'");
              break;
            case "shadow":
              // THe shadow <g> elements do NOT require an id
              break;
            default:      // Other node
              lHtml.push("id='" + options['type'] + "_" + oThis['id'] + "'");
              break;
          }
          // Add the @class
          switch (options['type']) {
            case "tree_leaf": sClass = "lithium-tree"; break;
            case "conn_leaf": sClass = "lithium-conn"; break;
            case "node_leaf": sClass = "lithium-node"; break;
            default:
              sClass = "lithium-" + options['type'];
              if (options.hasOwnProperty("root") && option['root'] === true) {
                sClass += " lithium-root";
              }
              break;
          }
          lHtml.push("class='" +sClass + "'");
          // Optional" with, height, x, y
          if (options.hasOwnProperty("x")) { lHtml.push("x='" + options['x'] + "'");}
          if (options.hasOwnProperty("y")) { lHtml.push("y='" + options['y'] + "'"); }
          if (options.hasOwnProperty("width")) { lHtml.push("width='" + options['width'] + "'"); }
          if (options.hasOwnProperty("height")) { lHtml.push("height='" + options['height'] + "'"); }
          // Finish the element
          lHtml.push(">");
          // REturn the element
          return lHtml.join(" ");
        } catch (ex) {
          // Show error message
          private_methods.showError("getG", ex);
          // Return empty string
          return "";
        }
      },
      /**
       * verticalDrawTree
       *    Position everything under <g class='lithium-root'> node [el] 
       *    and then return the total width of the children under me
       * 
       * @param {type} el
       * @param {type} shiftLeft
       * @param {type} shiftTop
       * @returns {undefined}
       */
      verticalDrawTree: function (el, shiftLeft, shiftTop) {
        var verticalDelta = branchHeight,
            childrenWidth = 0,
            returned = 0,
            thisX = 0,
            thisY = 0,
            parWidth = 0,
            shiftAdd = 0,
            space = " ";

        try {
          // Validate
          if (el === undefined || shiftLeft === undefined || shiftTop === undefined) return -1;

          // Applied vertical shift of the child depends on the Height of the containernode
          // Adapt the recursion level
          level += 1;

          // Get the text of this element
          var sElText = private_methods.getText(el);

          // =========== Debugging ========================
          if (bDebug) console.log(level + ":" + space.repeat(level) + sElText + " sl=" + shiftLeft);
          // ==============================================

          // Fit node around text and get its width/height
          var containerNode = private_methods.fitRectangle(el);

          // ========== children's WIDTH ==========
          $(el).children(".lithium-tree").each(function () {
            // Is this node visible?
            if (private_methods.isVisible(this)) {
              if (branchHeight - containerNode['height'] < 30) {
                // If too close to the child: shift 40 units
                verticalDelta = containerNode['height'] + 40;
              }
              // Call myself, but now with this child
              returned = private_methods.verticalDrawTree(
                      this,
                      shiftLeft + childrenWidth,
                      shiftTop + verticalDelta);
              // Add the returned value
              childrenWidth += returned;
            }
            // Check: is length of the containerNode bigger than the total length of the children
            if (childrenWidth > 0 && containerNode['expanded']) {
              // Adapt the width of the children
              childrenWidth = Math.max(
                      // Was: childrenWidth + (containerNode['width']-childrenWidth)/2,
                      childrenWidth + Math.ceil((containerNode['width'] - childrenWidth) / 2),
                      // containerNode['width'],
                      childrenWidth);
            }
          });

          // Terminal nodes: Rectify zero
          if (childrenWidth === 0) {
            shiftAdd = 0;
            // Terminal nodes: calculate [shiftAdd] if parent is wider
            if ($(el).parent().is(".lithium-tree")) {
              // Find out what the width of the <g> 'lithium-tree' parent is
              parWidth = parseInt($(el).parent().attr("width"), 10);
              // Compare this width with 'my' original container width
              if (parWidth >= childrenWidth && parWidth >= containerNode['width']) {
                shiftAdd = (parWidth - containerNode['width']) / 2 + shadowDepth;
              }
            }
            // Terminal nodes need to have 'wordSpacing' added for beauty...
            childrenWidth = containerNode['width'] + wordSpacing; //  + shiftAdd;
          }

          // =========== Debugging ========================
          if (bDebug) console.log(level + ":" + space.repeat(level) + sElText + " cw=" + childrenWidth);
          // ==============================================

          // Rectify large containers
          if (containerNode['width'] > childrenWidth) {
            childrenWidth = containerNode['width'] + shadowDepth;
          }

          // ========== Positioning ===============
          thisY = shiftTop;
          // Find out exactly how many children there are
          var iChildNodes = $(el).children(".lithium-tree").length;
          // Are there any children and if the containerNode  is actually visible...
          if (iChildNodes > 0 && containerNode['expanded']) {
            // Get the parameters of the FIRST child
            var first = $(el).children(".lithium-tree").first();
            var firstLoc = private_methods.getLocation(first);
            // Action depends on the #number of children
            if (iChildNodes === 1) {
              // There is only one child
              // get this child
              thisX = firstLoc['x'] + Math.ceil((firstLoc['width'] - containerNode['width']) / 2) + shiftAdd;
            } else {
              var firstCenter = firstLoc['x'] + Math.ceil(firstLoc['width'] / 2);
              var last = $(el).children(".lithium-tree").last();
              var lastLoc = private_methods.getLocation(last);
              var lastCenter = lastLoc['x'] + Math.ceil(lastLoc['width'] / 2);
              thisX = Math.max(firstCenter,
                firstCenter + Math.ceil((lastCenter - firstCenter - containerNode['width']) / 2));
              // NOTE: the following is not good; it causes the connection not to center.
              // thisX -= Math.ceil(firstLoc['width']/2);
              thisX += shiftAdd;
            }
          } else {
            thisX = shiftLeft + shiftAdd;
          }

          // =========== Debugging ========================
          if (bDebug) console.log(level + ":" + space.repeat(level) + sElText + " thisX=" + thisX);
          // ==============================================

          // Set the new position of the container node
          containerNode['x'] = thisX;
          containerNode['y'] = thisY;
          private_methods.setLocation(el, containerNode);

          // Adapt the recursion level
          level -= 1;

          // Return the calculated childrenwidth
          return childrenWidth;
      } catch (ex) {
          private_methods.showError("verticalDrawTree", ex);
          return null;
        }

      },

      /**
       * fitRectangle
       *    Make sure the WIDTH of the rectangle fits to the text inside it
       * 
       * @param {type} el
       * @returns {undefined}
       */
      fitRectangle: function (el) {
        var oRect = {};
        var textWidth = 0;

        try {
          // Validate
          if (el === undefined) return oRect;
          if ($(el).is(".lithium-tree")) {
            // Get the node element
            var node = $(el).children(".lithium-node").first();
            // Is it visible?
            if (!private_methods.isVisible(el)) {
              // Get to the text
              var sText = $(node).children("text").first().text();
              textWidth = sText.length * 4;
            } else {
              textWidth = $(node).children("text").first().get(0).getBBox().width;
            }
            // var textWidth = $(node).children("text").first().get(0).getBBox().width;
            // Continue
            textWidth += 8;
            var myHeight = 0;
            // Set the width of the box to the correct value 
            $(node).find("rect").each(function () {
              $(this).attr("width", textWidth.toString());
              var h = parseInt($(this).attr("height"), 10);
              if (h > myHeight) myHeight = h;
            });
            oRect['width'] = textWidth;
            oRect['height'] = myHeight;
            oRect['expanded'] = private_methods.getExpanded(el);
            // Set these parameters in the <g> 
            $(el).attr("width", oRect['width']);
            $(el).attr("height", oRect['height']);
          }
          // Return the rectangle
          return oRect;
        } catch (ex) {
          private_methods.showError("fitRectangle", ex);
          return null;
        }
      },

      /**
       * setRectangle
       *    Set the elements associated with this rectangle to
       *    the indicated X and Y values
       * 
       * @param {type} el
       * @param {type} oRect
       * @returns {undefined}
       */
      setRectangle: function (el, oRect) {
        try {
          // Validate
          if (el === undefined) return;
          if ($(el).is(".lithium-tree")) {
            // Get the current coordinates
            var oCurrent = private_methods.getRect(el);
            // Calculate how much x and y need to be moved
            var move_x = parseInt(oCurrent['x'], 10) - parseInt(oRect['x'], 10);
            var move_y = parseInt(oCurrent['y'], 10) - parseInt(oRect['y'], 10);
            // Adjust this node's elements:
            // (1) this node's [node]
            $(el).children(".lithium-node").find("rect").each(function () {
              $(this).attr("x", parseInt($(this).attr("x"), 10) + move_x);
              $(this).attr("y", parseInt($(this).attr("y"), 10) + move_y);
            });
            // (2) this node's [toggle element
            $(el).children(".lithium-toggle").find("rect").each(function () {
              $(this).attr("x", parseInt($(this).attr("x"), 10) + move_x);
              $(this).attr("y", parseInt($(this).attr("y"), 10) + move_y);
            });
            $(el).children(".lithium-toggle").find("line").each(function () {
              $(this).attr("x1", parseInt($(this).attr("x1"), 10) + move_x);
              $(this).attr("y1", parseInt($(this).attr("y1"), 10) + move_y);
              $(this).attr("x2", parseInt($(this).attr("x2"), 10) + move_x);
              $(this).attr("y2", parseInt($(this).attr("y2"), 10) + move_y);
            });
            // (3) this node's connector
            $(el).children(".lithium-conn").find("line").each(function () {
              $(this).attr("x1", parseInt($(this).attr("x1"), 10) + move_x);
              $(this).attr("y1", parseInt($(this).attr("y1"), 10) + move_y);
              $(this).attr("x2", parseInt($(this).attr("x2"), 10) + move_x);
              $(this).attr("y2", parseInt($(this).attr("y2"), 10) + move_y);
            });
          }
        } catch (ex) {
          private_methods.showError("setRectangle", ex);
        }
      },

      isVisible: function (el) {
        try {
          var sDisplay = $(el).css("display");
          // && sDisplay !== "inline" && sDisplay !== ""
          return (sDisplay !== "none");
        } catch (ex) {
          private_methods.showError("isVisible", ex);
          return false;
        }
      },

      getExpanded: function (el) {
        try {
          // Validate
          if (!$(el).is(".lithium-tree")) return false;
          // Do I have the feature?
          if ($(el).hasOwnProperty("expanded")) {
            // Get its value
            return $(el).attr("expanded");
          } else {
            // Are my children visible?
            var oChildren = $(el).children(".lithium-tree");
            if (oChildren.length === 0) {
              // No children, so not expanded?
              return false;
            } else {
              // REturn the invisibility of the first child
              return private_methods.isVisible($(oChildren).first());
            }
          }
        } catch (ex) {
          private_methods.showError("getExpanded", ex);
          return false;
        }
      },

      /**
       * moveDiagram
       *    Move the whole diagram in the proposed direction
       * 
       * @param {type} el
       * @param {type} oMove
       * @returns {undefined}
       */
      moveDiagram: function (el, oMove) {
        try {
          // Select all the <rect> elements under me
          $(el).find(".lithium-tree").each(function () {
            $(this).attr("x", parseInt($(this).attr("x"), 10) + oMove['x']);
            $(this).attr("y", parseInt($(this).attr("y"), 10) + oMove['y']);
            // Debugging: immediately apply this location
            private_methods.applyOneLocation(this);
          });
        } catch (ex) {
          private_methods.showError("moveDiagram", ex);
        }
      },

      /**
       * getRect
       *    Get the x,y,w,h coordinates of this element
       * 
       * @param {type} el
       * @returns {RECT object}
       */
      getRect: function (el) {
        try {
          // Validate
          if (el !== undefined) {
            // Find first lithium-node under me
            var rect = $(root).find(".lithium-node rect").first();
            if (rect !== undefined) {
              // Create structure with x,y etc
              var oRect = {};
              oRect['x'] = parseInt($(rect).attr("x"), 10);
              oRect['y'] = parseInt($(rect).attr("y"), 10);
              oRect['width'] = parseInt($(rect).attr("width"), 10);
              oRect['height'] = parseInt($(rect).attr("height"), 10);
              oRect['expanded'] = private_methods.isVisible(el);
              return oRect;
            }
          }
          return null;
        } catch (ex) {
          private_methods.showError("getRect", ex);
          return null;
        }

      },
      getRectSize: function (el, sType) {
        try {
          if (sType === undefined || sType === "")
            sType = "rect";
          // validate
          if (el !== undefined) {
            // Must be a rect
            if ($(el).is(sType)) {
              // Create structure with x,y etc
              var oRect = {};
              oRect['x'] = parseInt($(el).attr("x"), 10);
              oRect['y'] = parseInt($(el).attr("y"), 10);
              oRect['width'] = parseInt($(el).attr("width"), 10);
              oRect['height'] = parseInt($(el).attr("height"), 10);
              oRect['expanded'] = private_methods.isVisible(el);
              return oRect;
            }
          }
          return null;
        } catch (ex) {
          private_methods.showError("getRectSize", ex);
          return null;
        }
      }
    };
    // Methods that are exported by [crpstudio.project] for others
    return {
      /**
       * treeToSvg
       *    Convert a JSON representation of a syntax tree to SVG
       * 
       * @param {element} svgDiv  - DOM where tree must come
       * @param {object} oTree    - The tree as an object
       * @param {element} errDiv  - DOM where error may appear
       * @returns {boolean}
       */
      treeToSvg: function( svgDiv, oTree, errDiv) {
        var oMove = { x: 0, y: 0 },
            arCol = ["black", "darkgoldenrod", "darkgreen", "gainsboro", "ivory", "lightblue",
                     "lightgreen", "linen", "purple", "steelblue", "white", "whitesmoke"],
            i,                      // Counter
            lHtml = [];

        try {
          // Validate
          if (svgDiv === undefined || oTree === undefined) return false;
          if (errDiv === undefined) errDiv = svgDiv;
          // Treat the tree: add parent, level and unique numerical id's
          private_methods.setParentAndId(oTree, null, 0);
          // Other initialisations
          loc_arLeaf = [];
          root = null;
          $(svgDiv).html(private_methods.initSvg());
          // Hierarchically build an SVG picture based on [oTree]
          root = private_methods.nodeToSvg(oTree, svgDiv);
          // Return positively
          return true;
        } catch (ex) {
          // Show the error at the indicated place
          $(errDiv).html("treeToSvg error: " + ex.message);
          return null;
        }
      },
      /**
       * drawTree
       *    Mimic the LithiumControl.DrawTree() method, starting at [el]
       * 
       * @param {element} svgDiv
       * @returns {boolean}
       */
      drawTree: function (svgDiv) {
        var oMove = { x: 0, y: 0 };

        // Validate
        if (svgDiv === undefined) return false;
        // Find the root: the top <g> node
        root = $(svgDiv).find("g.lithium-root").first();
        if (root === undefined || root === null) return false;
        // Center the <g> coordinates of the root
        private_methods.fitRectangle(root);
        private_methods.centerRoot(root);
        // Store the location of the root
        var p = private_methods.getLocation(root);
        if (p !== undefined && p !== null) {
          var parent = $(root).parent();
          // Set the graphabstract to the root
          graphAbstract['root'] = p;
          // Perform a re-drawing, starting from the root downwards
          level = 0;
          private_methods.verticalDrawTree(root, marginLeft, p['y']);
          // Calculate how much must be moved
          oMove['x'] = p['x'] - parseInt($(root).attr('x'), 10);
          oMove['y'] = p['y'] - parseInt($(root).attr('y'), 10);
          // Move the whole
          private_methods.moveDiagram(parent, oMove);

          // Calculate maxY
          var maxY = 0;
          $(parent).find(".lithium-tree").each(function () {
            if ((private_methods.isVisible(this)) &&
                    $(this).children(".lithium-tree").length === 0) {
              var this_y = parseInt($(this).attr("y"), 10);
              if (this_y > maxY) maxY = this_y;
            }
          });
          // Move all items in the y-direction
          $(parent).find(".lithium-tree").each(function () {
            if ((private_methods.isVisible(this)) &&
                    $(this).children(".lithium-tree").length === 0) {
              $(this).attr("y", maxY);
              // Debugging: immediately apply this location
              private_methods.applyOneLocation(this);
            }
          });

          // Calculate a minPoint
          var minPoint = { x: 1000000, y: 1000000 };
          var maxSize = { width: 0, height: 0 };
          // Walk over all shapes
          $(parent).find(".lithium-tree").each(function () {
            if (private_methods.isVisible(this)) {
              var oThisRect = private_methods.getLocation(this);
              var iNewWidth = oThisRect['x'] + oThisRect['width'];
              var iNewHeight = oThisRect['y'] + oThisRect['height'];

              // Look for max width / max height
              maxSize['width'] = Math.max(iNewWidth, maxSize['width']);
              maxSize['height'] = Math.max(iNewHeight, maxSize['height']);

              // Look for minimum size
              minPoint['x'] = Math.min(minPoint['x'], oThisRect['x']);
              minPoint['y'] = Math.min(minPoint['y'], oThisRect['y']);
            }
          });

          // Move the whole diagram, teking into account [minPoint]
          oMove['x'] = 50 - minPoint['x'];
          oMove['y'] = 50 - minPoint['y'];
          private_methods.moveDiagram(parent, oMove);

          // Apply the changes in x,y,w,h to all elements
          private_methods.applyLocations(parent, "loc");

          // Apply the changes in x,y,w,h to all elements
          private_methods.applyLocations(parent, "conn");

          // Adapt maxSize again
          maxSize['width'] = maxSize['width'] - minPoint['x'] + 100;
          maxSize['height'] = maxSize['height'] - minPoint['y'] + 100;
          // Also adapt the SVG's width and height
          var svg = $(svgDiv).find("svg").first();
          $(svg).attr("width", maxSize['width'].toString() + 'px');
          $(svg).attr("height", maxSize['height'].toString() + 'px');

          // Attach an event handler to all the toggles
          $(svg).find(".lithium-toggle rect, line").click(function () { crpstudio.tree.toggle(this); });
        }
        // All went well
        return true;
      },

      /**
       * toggle
       *    Behaviour when I am toggled
       * 
       * @param {element} elRect
       * @returns {undefined}
       */
      toggle: function (elRect) {
        var bVisible,   // VIsibility
          elSvg,        // The SVG root of the tree
          elToggle,     // The .lithium-toggle element
          elVbar,       // My own vertical bar
          elTree;       // The tree I am in

        // Get vertical bar and my tree
        elToggle = $(elRect).parent();
        elVbar = $(elToggle).children(".lithium-vbar");
        elTree = $(elToggle).parent();
        elSvg = $(elRect).closest("svg");
        // Get my status
        bVisible = private_methods.isVisible(elVbar);
        // Action depends on visibility
        if (bVisible) {
          // Bar is visible: close it
          private_methods.classAdd(elVbar, "hidden");
          // Make all children visible again
          $(elTree).find(".lithium-tree").each(function () {
            private_methods.classRemove(this, "hidden");
          });
          // Adapt [expanded] state
          $(elTree).attr("expanded", true);
        } else {
          // Bar is invisible: show it
          private_methods.classRemove(elVbar, "hidden");
          // Make all children invisible
          $(elTree).find(".lithium-tree").each(function () {
            private_methods.classAdd(this, "hidden");
          });
          // Adapt [expanded] state
          $(elTree).attr("expanded", false);
        }
        // Now make sure the whole tree is re-drawn
        crpstudio.tree.drawTree($(elSvg).parent());
      }

    };
  }($, crpstudio.config));

  return crpstudio;

}(jQuery, window.crpstudio || {}));
