/**
 * Copyright (c) 2017 Radboud University Nijmegen.
 * All rights reserved.
 *
 * @author Erwin R. Komen
 */

/*globals jQuery, crpstudio, Crpstudio, alert: false, */
var crpstudio = (function ($, crpstudio) {
  "use strict";
  crpstudio.svg = (function ($, config) {
    // Local variables within crpstudio.svg
    var marginLeft = 10,      // Margin of whole figure
        wordSpacing = 12,     // Space between nodes
        branchHeight = 70,    // Height between branches
        shadowDepth = 5,      // How thick the shadow is
        bDebug = false,       // Debugging set or not
        level = 0,            // Recursion level of vertical draw tree
        graphAbstract = {},   // Representation of the total
        width = 1025,         // Initial canvas width
        height = 631,         // Initial canvas height
        loc_svgRoot = null,
        loc_oNode = {},       // Local version of current node tree
        loc_errDiv = null,    // Where to show errors
        loc_arLeaf = [],      // Storage of pointers to the LEAFs of the tree
        loc_iTreeId = 0,      // Available ID's for tree
        loc_iShadow = 3,      // 
        loc_iMargin = 5,      // margin of box around tree image
        loc_iToggle = 10,     // Width and height of toggle
        loc_iWidth = 0.5,     // Stroke-width in 
        loc_iMaxLevel = 0,    // Maximum hierarchical level of this tree
        loc_iDistVert = 60,   // Vertical distance between tree nodes
        loc_iDistHor = 10,     // Minimal distance between end nodes
        loc_iCurrentNode = -1, // ID of the currently selected node
        loc_bKeep = false,    // Stay on fixed position
        root = null;          // Root of the tree (DOM position)

    // Methods that are local to [crpstudio.dbase]
    var private_methods = {
      /**
       * showError
       *     Show the error at the indicated place
       */
      showError: function (sFunction, ex) {
        var sOld = "",
            sMsg = "Error in " + sFunction + ": " + ex.message;

        if (loc_errDiv !== undefined && loc_errDiv !== null) {
          sOld = $(loc_errDiv).html();
          $(loc_errDiv).html(sOld + "<p><code>"+sMsg+"</code></p>");
        }
      },
      setErrLoc: function(sLoc) {
        loc_errDiv = sLoc;
        if (sLoc.indexOf("#")!==0) {
          loc_errDiv = "#" + loc_errDiv;
        }
        // Clear the errors
        $(loc_errDiv).html();
      },
      setSvgRoot : function(sSvgRoot) {
        loc_svgRoot = sSvgRoot;
      },
      setNodeTree : function(oThis) {
        loc_oNode = oThis;
      },
      /**
       * fitFeatureBox
       *    Initialize the <svg> in the @sDiv
       * 
       * @param {object} oBound
       * @param {el} elTarget
       * @returns {object}
       */
      fitFeatureBox: function (oBound, elTarget) {
        var rect = null;

        try {
          // Take into account scrolling
          oBound['x'] -= document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] -= document.documentElement.scrollTop || document.body.scrollTop;
          // Make sure it all fits
          if (oBound['x'] + $(elTarget).width() + oBound['width'] +10> $(window).width()) {
            oBound['x'] -= $(elTarget).width() + oBound['width'];
          } else if (oBound['x'] < 0) {
            oBound['x'] = 10;
          }
          if (oBound['y'] + $(elTarget).height() + oBound['height'] +10 > $(window).height()) {
            oBound['y'] -= $(elTarget).height() + oBound['height'];
          } else if (oBound['y'] < 0) {
            oBound['y'] = 10;
          } else {
            oBound['y'] += oBound['height'] + 10;
          }
          // Take into account scrolling
          oBound['x'] += document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] += document.documentElement.scrollTop || document.body.scrollTop;
          return oBound;
        } catch (ex) {
          private_methods.showError("fitFeatureBox", ex);
          return oBound;
        }
      },
      /**
       * screenCoordsForRect
       *    Get the correct screen coordinates for the indicated <svg> <rect> element
       * 
       * @param {el} svgRect
       * @returns {object}
       */
      screenCoordsForRect: function (svgRect) {
        var pt = null,
            elSvg = null,
            rect = null,
            oBound = {},
            matrix;
            
        try {
          // Get the root <svg>
          elSvg = $(svgRect).closest("svg").get(0);

          rect = svgRect.get(0);
          oBound = rect.getBoundingClientRect();

          // Take into account scrolling
          oBound['x'] += document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] += document.documentElement.scrollTop || document.body.scrollTop;
          return oBound;
        } catch (ex) {
          private_methods.showError("screenCoordsForRect", ex);
          return oBound;
        }

      },
      /**
       * initSvg
       *    Initialize the <svg> in the @sDiv
       * 
       * @param {el} sDiv
       * @returns {bool}
       */
      initSvg: function (sDiv) {
        var lHtml = [],   // Where we combine SVG
            svgDiv = null,
            svgDoc = null,
            sHtml = "",
            arCol = ["black", "darkgoldenrod", "darkgreen", "gainsboro", "ivory", "lightblue",
                     "lightgreen", "linen", "purple", "steelblue", "white", "whitesmoke"],
            i;            // Counter

        try {
          /* 
          // Start creating an SVG document
          svgDiv = document.createElementNS("http://www.w3.org/1999/xhtml", "div");
          $(sDiv).append(svgDiv);
          svgDoc = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          svgDoc.setAttribute("width", "1047");
          svgDoc.setAttribute("height", "542");
          $(sDiv).find("div").append(svgDoc); */
          /* */
          // Create an <svg> element
          lHtml.push("<svg width=\"1047px\" height=\"542px\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\">");
          /* */
          // Create defs
          lHtml.push("<defs >");
          for (i = 0; i < arCol.length; i++) {
            lHtml.push("<linearGradient id=\"" + arCol[i] + "_gradient\"><stop offset=\"5%\" stop-color=\"" + arCol[i] + "\" />");
            lHtml.push("<stop offset=\"95%\" stop-color=\"whitesmoke\" /></linearGradient>");
          }
          lHtml.push("</defs>");
          // Finish the tree
          lHtml.push("</svg>");
          sHtml = lHtml.join("\n");
          //  OLD: $(sDiv).html(sHtml);
          sHtml = jQuery.parseXML(sHtml);
          // REPLACE whatever was there
          $(sDiv).html(sHtml.documentElement);
          return true;
        } catch (ex) {
          private_methods.showError("initSvg", ex);
          return false;
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
      getTreeId: function () { loc_iTreeId += 1; return loc_iTreeId; },
      /**
       * getNode
       *    Find the node with the indicated id
       * 
       * @param {object} oTree
       * @param {int}    iNodeId
       * @returns {object}
       */
      getNode: function (oTree, iNodeId) {
        var i = 0,
            oBack = {};

        try {
          if (oTree.id === iNodeId) {
            return oTree;
          } else if (oTree.hasOwnProperty("child") && oTree['child'].length > 0) {
            // Walk children
            for (i = 0; i < oTree['child'].length; i++) {
              oBack = private_methods.getNode(oTree['child'][i], iNodeId);
              if (oBack !== null) {
                return oBack;
              }
            }
          }
          return null;
        } catch (ex) {
          private_methods.showError("getNode", ex);
          return null;
        }
      },
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
       * @param {type} gThis
       * @param {type} oRect
       * @returns {Boolean}
       */
      setLocation: function (gThis, oRect) {
        try {
          // Validate: exist and must be <g> with class "lithium-tree"
          if (gThis === undefined) return false;
          if (!$(gThis).is(".lithium-tree")) return false;
          /*
          $(el).attr("x", oRect['x']);
          $(el).attr("y", oRect['y']);
          // Optionally set width and height
          if (oRect.hasOwnProperty("width")) { $(el).attr("width", oRect['width']); }
          if (oRect.hasOwnProperty("height")) { $(el).attr("height", oRect['height']); }
          // Debugging: immediately apply this location
          private_methods.applyOneLocation(el);
          */

          // Get my main components
          var node = $(gThis).children(".lithium-node").first();
          // The [node] contains: [rect], [shadow] and [text]
          var mainRect = $(node).children("rect").first();
          var shadowRect = $(node).children(".lithium-shadow").children("rect").first();
          var mainText = $(node).children("text").first();
          // Calculate the shift
          var shift_x = oRect['x'] - parseInt($(mainRect).attr("x"), 10);
          var shift_y = oRect['y'] - parseInt($(mainRect).attr("y"), 10);
          var new_w = oRect['width'];
          var new_h = oRect['height'];
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
          //var oSrc = private_methods.getRectSize(gSrc, ".lithium-tree");
          //var oDst = private_methods.getRectSize(gDst, ".lithium-tree");
          var oSrc = private_methods.getRect(gSrc);
          var oDst = private_methods.getRect(gDst);
          if (oSrc === null || oDst === null) return "";
          // Make sure the destination is not too large
          oDst['y'] = oDst['y'] + loc_iToggle;
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
       * svgText
       *    Construct a <text> element according to the parameters in [oRect]
       * 
       * @param {type} oRect
       * @returns {undefined}
       */
      svgText: function (oRect) {
        try {
          // Validate
          if (!oRect.hasOwnProperty("x") || !oRect.hasOwnProperty("y") ||
              !oRect.hasOwnProperty("text")) return "[TEXT-ERROR]";
          // Add default arguments if  needed
          if (!oRect.hasOwnProperty("font-family")) oRect['font-family'] = "Verdana";
          if (!oRect.hasOwnProperty("font-size")) oRect['font-size'] = "12";
          if (!oRect.hasOwnProperty("fill")) oRect['fill'] = "black";
          // Now create the svg stuff
          var sBack = "<text x=\"" + (oRect['x'] + 5) +
                          "\" y=\"" + (oRect['y'] + 15) +
                          "\" font-family=\"" + oRect['font-family'] +
                          "\" font-size=\"" + oRect['font-size'] + 
                          "\" fill=\"" + oRect['fill'] +
                          "\">" + oRect['text'] + "</text>";
          // Return what we made
          return sBack;
        } catch (ex) {
          private_methods.showError("svgText", ex);
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
        var sR = "";

        try {
          // Validate
          if (!oRect.hasOwnProperty("x") || !oRect.hasOwnProperty("y") ||
              !oRect.hasOwnProperty("width") || !oRect.hasOwnProperty("height")) return "[RECT-ERROR]";
          // Add default arguments if  needed
          if (!oRect.hasOwnProperty("stroke")) oRect['stroke'] = "black";
          if (!oRect.hasOwnProperty("stroke-width")) oRect['stroke-width'] = "0.5";
          if (!oRect.hasOwnProperty("fill")) oRect['fill'] = "white";
          // Do we need to add the R?
          if (oRect.hasOwnProperty("rx") && oRect.hasOwnProperty("ry")) {
            sR = " rx=\"" + loc_iShadow + "\"" +
                 " ry=\"" + loc_iShadow + "\"";
          }
          // Now create the svg stuff
          var sBack = "<rect x=\"" + oRect['x'] +
                          "\" y=\"" + oRect['y'] + "\"" + sR +
                          " width=\"" + oRect['width'] +
                          "\" height=\"" + oRect['height'] +
                          "\" fill=\"" + oRect['fill'] +
                          "\" stroke=\"" + oRect['stroke'] +
                          "\" stroke-width=\"" + oRect['stroke-width'] + "\" />";
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

          return private_methods.svgRect({
            x: x + loc_iShadow, y: y + loc_iShadow, width: w, height: h, rx: loc_iShadow, ry: loc_iShadow,
            fill: "gainsboro", stroke: "gainsboro", 'stroke-width': loc_iWidth
          });
        } catch (ex) {
          private_methods.showError("rectShadow", ex);
          return "";
        }
      },
      textNode: function (options) {
        var x, y, t;

        try {
          // Get the coordinates
          x = options['x'];
          y = options['y'];
          t = options['t'];
          return private_methods.svgText({
            x: x, y: y, text: t
          });
        } catch (ex) {
          private_methods.showError("textNode", ex);
          return "";
        }        
      },
      rectNode : function(options) {
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
            case "end_star": sColor = "url(#lightgreen_gradient)"; break;
            case "node": sColor = "url(#steelblue_gradient)"; break;
            case "sel": sColor = "url(#darkgoldenrod_gradient)"; break;
          }

          return private_methods.svgRect({
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
          var sLine = "<line x1=\"" + x1 +
                      "\" y1=\"" + y1 + "\" x2=\"" + x2 +
                      "\" y2=\"" + y2 + "\" stroke=\"black\" stroke-width=\"0.5\" />";
          if (bHidden) {
            sLine = "<g class=\"lithium-vbar hidden\">" +
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
      getGwidth : function(el) {
        try {
          if (el === undefined || el === null) return 0;
          var elRect = $(el).find("rect");
          if ($(elRect).length > 0) {
            return $(elRect).first().attr("width");
          } else {
            return 0;
          }
        } catch (ex) {
          private_methods.showError("getGwidth", ex);
          return 0;
        }
      },
      appendSvg : function(el, sSvg) {
        try {
          var sTree = jQuery.parseXML(sSvg.replace(/&/g, "&amp;"));
          // OLD $(dParent).append(sTree);
          $(el).append(sTree.documentElement);
          // Refresh
          $(el).html($(el).html());
          return true;
        } catch (ex) {
          return false;
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
            iLen = 0,     // Number of elements
            sClass = "",
            sText = "",   // Text for this node
            sPos = "",    // POS for this node
            sTree = "",   // Text of <g> 'tree'   part
            sNode = "",   // Text of <g> 'node'   part
            sToggle = "", // Text of <g> 'toggle' part
            sConn = "",   // Text of <g> 'conn'   part
            svgRect = "",
            svgText = "",
            sId = "",
            dNode = null, // Current SVG DOM master element
            dLeaf = null, // SVG DOM leaf element
            dPrev = null, // Preceding DOM leaf element
            dPrevP = null,// Parent of dPrev
            dChildren = [], // My child nodes
            dChild = null,  // One child
            dLast = null,   // Last child
            oChild = null,  // One [oNode] child
            oPos = {},      // General purpose position object
            oPosN = {},     // Position of the node
            oRect = {},     // General purpose
            oRectP = {},
            oRectL = {},
            oRectN = {},
            bCollapsed = false,
            patt = new RegExp("tree_leaf.*"),
            sType = "",     // The type of situation we are in
            oChild = {};    // One child of [oNode]

        try {
          // Validate
          if (oNode === undefined) return "";
          if (!oNode.hasOwnProperty("pos") || !oNode.hasOwnProperty("level") || !oNode.hasOwnProperty("id")) return "";
          // Get the POS of the node
          sPos = oNode['pos'];
          // Create an svg <g> element that contains its ID and CLASS
          sTree = private_methods.getLithiumNode({ el: oNode, type: "node" });
          // OLD $(dParent).append(sTree);
          private_methods.appendSvg(dParent, sTree);
          dNode = $(dParent).children().last();
          // Copy the 'expanded' attribute, if available in the node
          if (oNode.hasOwnProperty("expanded")) {
            $(dNode).attr("expanded", oNode['expanded']);
          } else {
            $(dNode).attr("expanded", true);
          }

          // Debugging
          if (oNode['expanded'] === false || $(dNode).attr("expanded") === "false") {
            var iStop = 1;
          }

          // Now FIRST walk all my children (if there are any)
          if (oNode.hasOwnProperty("child") && $(dNode).attr("expanded") === "true") {
            iLen = oNode['child'].length;
            for (i = 0; i < iLen; i++) {
              // Treat this child
              oChild = oNode['child'][i];
              dChild = private_methods.nodeToSvg(oChild, dNode);
            }
          }

          // Debugging
          if (oNode['expanded'] === false || $(dNode).attr("expanded") === "false") {
            var iStop = 1;
          }

          // Once all the child nodes have been done, we can continue...
          // Fit the text in the node (and this also sets the 'width' and 'height' of the <g> element)
          private_methods.fitRectangle(dNode);
          oRectN = private_methods.getRect(dNode);
          // Set the node's w/h
          oPosN['width'] = oRectN['width'];
          oPosN['height'] = oRectN['height'];
          oPosN['y'] = oNode['level'] * loc_iDistVert + loc_iMargin;
          // What is the situation
          sType = (oNode.hasOwnProperty("child")) ? "node" : "terminal";
          if (!oNode['expanded']) sType += "_collapsed";
          switch (sType) {
            case "node_collapsed":
            case "terminal_collapsed":
              // This is an end-node, but not one with text, but only with a POS label
              // Determine the [x] for this node
              if (loc_arLeaf.length === 0) {
                // THis is te first terminal node
                x = loc_iMargin;
              } else {
                // Get the first preceding tree/leaf combination
                dPrev = loc_arLeaf[loc_arLeaf.length - 1]; dPrevP = $(dPrev).parent();
                oRect = private_methods.getRect(dPrev);
                oRectP = private_methods.getRect(dPrevP);
                // Get the rightmost point of this leaf or its parent node
                x = Math.max(oRect['x'] + oRect['width'], oRectP['x'] + oRectP['width']) + loc_iDistHor;
              }
              oPosN['x'] = x;
              // Place [dNode] to this new position
              private_methods.setLocation(dNode, oPosN);
              // Make sure the vbar is shown
              private_methods.classRemove($(dNode).children(".lithium-toggle").children(".lithium-vbar"), "hidden");

              // Store this node as if it were a LEAF node in the global list for future reference
              loc_arLeaf.push(dNode);
              break;
            case "terminal":
              // THis is an end-node: it must contain text
              if (!oNode.hasOwnProperty("txt")) return "";
              // Create an SVG 'lithium-node'
              sNode = private_methods.getLithiumNode({ el: oNode, type: 'terminal' });
              // Add this leaf node under [dNode]
              // OLD dLeaf = $(dNode).append(sNode);
              private_methods.appendSvg(dNode, sNode);
              dLeaf = $(dNode).children().last();

              // Fit the text in the leaf
              private_methods.fitRectangle(dLeaf);
              oRectL = private_methods.getRect(dLeaf);
              // The w,h are needed for 'setLocation'
              oPos['width'] = oRectL['width'];
              oPos['height'] = oRectL['height'];
              // Determine the x,y for the leaf
              if (loc_arLeaf.length === 0) {
                // This is the first terminal
                x = loc_iMargin;
                // TODO: differentiate between two types of end-nodes: Vern+Punct versus Zero+Star
                oPos['y'] = (loc_iMaxLevel + 1) * loc_iDistVert + loc_iMargin;
              } else {
                // Get the first preceding tree/leaf combination
                dPrev = loc_arLeaf[loc_arLeaf.length - 1];
                oRect = private_methods.getRect(dPrev);
                // Is this a real leaf or a node?
                sId = $(dPrev).attr("id");
                bCollapsed = !patt.test(sId);
                if (bCollapsed) {
                  // Not a terminal node, but a collapsed node
                  x = oRect['x'] + oRect['width'] + loc_iDistHor;
                } else {
                  dPrevP = $(dPrev).parent();
                  oRectP = private_methods.getRect(dPrevP);
                  // Get the rightmost point of this leaf or its parent node
                  x = Math.max(oRect['x'] + oRect['width'], oRectP['x'] + oRectP['width']) + loc_iDistHor;
                }
                if (oNode['txt'].indexOf("*") === 0 || oNode['txt'] == "0") {
                  // The vertical position of [dLeaf] is determined by the level for *T* and 0
                  oPos['y'] = (oNode['level'] + 1) * loc_iDistVert + loc_iMargin;
                } else {
                  // Otherwise it is determine by the max
                  oPos['y'] = (loc_iMaxLevel + 1) * loc_iDistVert + loc_iMargin;
                }
              }
              // Set the x,y of [dLeaf] and its parent [dNode]
              if (oPos['width'] > oPosN["width"]) {
                // First dLeaf
                oPos['x'] = x;
                private_methods.setLocation(dLeaf, oPos);
                // Adapt x position of the parent [dNode]
                oPosN['x'] = oPos['x'] + oRectL['width'] / 2 - oRectN['width'] / 2;
                // Set the location of the node
                private_methods.setLocation(dNode, oPosN);
              } else {
                // First set the location of the dNode
                oPosN['x'] = x;
                private_methods.setLocation(dNode, oPosN);
                // Then determine the location of the leaf
                oPos['x'] = oPosN['x'] + oRectN['width'] / 2 - oRectL['width'] / 2;
                private_methods.setLocation(dLeaf, oPos);
              }             
              // Store the LEAF node in the global list for future reference
              loc_arLeaf.push(dLeaf);
              break;
            default:  // Normal nodes
              // THis assumes *ALL* the child nodes have alread been dealt with, so 'I' am the parent of all the nodes under me
              // (1) How many children do I have?
              dChildren = $(dNode).children(".lithium-tree");
              iLen = $(dChildren).length;
              if (iLen === 1) {
                // My x,y are totally dependant upon my one child's x,y
                dChild = $(dChildren).first();
                oPosN['x'] = private_methods.getCenter(dChild) -
                             oRectN['width'] / 2;
              } else if (iLen>1) {
                // There is more than 1 child
                // Calculate the average between the first and last child
                dChild = $(dChildren).first();
                dLast = $(dChildren).last();
                oPosN['x'] = (private_methods.getCenter(dLast) +
                              private_methods.getCenter(dChild)) / 2 -
                              oRectN['width']  / 2;
              } 
              // Place [dNode] to this new position
              private_methods.setLocation(dNode, oPosN);
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
      getCenter : function (el) {
        var center = 0,
            oRect = {};

        try {
          // Validate 
          if (el === undefined) return 0;
          oRect = private_methods.getRect(el);
          center = oRect['x'] + oRect['width'] / 2;
          return center;
        } catch (ex) {
          // Show error message
          private_methods.showError("getCenter", ex);
          return 0;
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
            lFeat = [],   // List of features in HTML
            sText = "",
            el,
            oFeat = {},   // Feature object
            x = 10,
            y = 10,
            w = 100,
            h = 22,
            sTerminal,    // Kind of terminal node
            sType;

        try {
          // Get obligatory parameters
          sType = options['type'];
          el = options['el'];
          // Get all features (if any)
          oFeat = el['f'];
          // Action depends on type
          switch (sType) {
            case "terminal":  // This is a terminal node
              // Get the text of the node
              sText = el['txt'];
              // Add a 'tree_leaf'  element
              lHtml.push(private_methods.getGstart({ type: "tree_leaf", el: el }));
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
              if (el.hasOwnProperty("type")) {
                sTerminal = (el['type'] === "Vern" || el['type'] === "Punct") ? "end" : "end_star";
              } else {
                sTerminal = "end";
              }
              lHtml.push(private_methods.rectNode({ x: x, y: y, w: w, h: h, type: sTerminal }));
              // Add a <text> node
              lHtml.push(private_methods.textNode({ x: x, y: x, t: sText }));
              // Finish the 'node_leaf'
              lHtml.push("</g>");
              // Finish the 'tree_leaf'
              lHtml.push("</g>");
              break;
            default:          // THis is a non-terminal node
              // The text of the node is the POS
              sText = el['pos'];
              // Add a 'tree'  element
              lHtml.push(private_methods.getGstart({ type: "tree", el: el }));
              if (el.parent !== null) {
                // Add a <g> 'lithium-conn' part: connection with the parent
                lHtml.push(private_methods.getGstart({ type: "conn", el: el }));
                // Finish the 'lithium-conn' part
                lHtml.push("</g>");
              }

              // Add a <g> 'lithium-node' part + its shadow
              lHtml.push(private_methods.getGstart({ type: "node", el: el }));

              // Within the 'lithium-node' there is a SHADOW:
              lHtml.push(private_methods.getGstart({ type: "shadow", el: el }));
              // Add a <rect> element to realise the shadow
              lHtml.push(private_methods.rectShadow({ x: x, y: y, w: w, h: h }));
              // Finish the shadow
              lHtml.push("</g>");

              // Within the 'lithium-node there is a RECT and TEXT
              lHtml.push(private_methods.rectNode({ x: x, y: y, w: w, h: h, type: "node" }));
              // Add a <text> node
              lHtml.push(private_methods.textNode({ x: x, y: x, t: sText }));

              // Finish the 'node'
              lHtml.push("</g>");

              // Add a 'lithium-toggle' element
              lHtml.push(private_methods.getGstart({ type: "toggle", el: el }));
              // And the toggle contains a RECT and a LINE
              lHtml.push(private_methods.rectNode({ x: x+w/2-loc_iToggle/2, y: y+h, w: loc_iToggle, h: loc_iToggle, type: "node" }));
              lHtml.push(private_methods.svgLine(10, 10, 18, 10, false));
              // Finish the 'toggle' element
              lHtml.push("</g>");

              // Finish the 'tree' element
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
       *  @return {bool}      - Used for errors
       */
      setParentAndId : function (o, p, iLevel) {
        var n = null,   // object node
            i = 0;      // counter

        try {
          // CHeck for level
          if (p===null) loc_iMaxLevel = 0;
          // Check for ID
          if (!o.hasOwnProperty("id")) { o['id'] = private_methods.getTreeId(); }
          // Check for level
          if (!o.hasOwnProperty("level")) { o['level'] = iLevel; }
          // Check for expanded
          if (!o.hasOwnProperty("expanded")) { o['expanded'] = true; }
          // CHeck for parent
          if (!o.hasOwnProperty("parent")) { o['parent'] = p;}
          // Check for children
          if (o.hasOwnProperty('child') && o['child'] !== null) {
            // Go one level down
            iLevel += 1;
            if (iLevel > loc_iMaxLevel) {loc_iMaxLevel = iLevel;}
            // Treat all children
            for (i = 0; i < o.child.length;i++) {
              // Treat this particular child
              if (!private_methods.setParentAndId(o['child'][i], o, iLevel)) {
                return false;
              }
            }
            // Go one level up again
            iLevel -= 1;
          }
          // Return success
          return true;
        } catch (ex) {
          // Show error message
          private_methods.showError("setParentAndId", ex);
          // Return false
          return false;
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
              lHtml.push("id=\"" + options['type'] + "_" + oThis['id'] + "_" + oParent['id'] + "\"");
              break;
            case "shadow":
              // THe shadow <g> elements do NOT require an id
              break;
            default:      // Other node
              lHtml.push("id=\"" + options['type'] + "_" + oThis['id'] + "\"");
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
          lHtml.push("class=\"" + sClass + "\"");
          // Optional" with, height, x, y
          if (options.hasOwnProperty("x")) { lHtml.push("x=\"" + options['x'] + "\""); }
          if (options.hasOwnProperty("y")) { lHtml.push("y=\"" + options['y'] + "\""); }
          if (options.hasOwnProperty("width")) { lHtml.push("width=\"" + options['width'] + "\""); }
          if (options.hasOwnProperty("height")) { lHtml.push("height=\"" + options['height'] + "\""); }
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
              try {
                textWidth = $(node).children("text").first().get(0).getBBox().width;
              } catch (ex) {
                var sText = $(node).children("text").first().text();
                textWidth = sText.length * 4;
              }
            }
            // var textWidth = $(node).children("text").first().get(0).getBBox().width;
            // Continue
            textWidth += 9;
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
            /* May not put X and Y in <g>
            // Set these parameters in the <g> 
            $(el).attr("width", oRect['width']);
            $(el).attr("height", oRect['height']);
            */
          }
          // Return the rectangle
          return oRect;
        } catch (ex) {
          private_methods.showError("fitRectangle", ex);
          return null;
        }
      },
      setMaxSize: function (oRect) {
        var svgDiv = loc_svgRoot;

        try {
          if (svgDiv === undefined || oRect === undefined) return false;
          if (!oRect.hasOwnProperty("width") || !oRect.hasOwnProperty("height")) return false

          // Adapt the max to include a margin
          oRect['width'] += loc_iMargin;
          oRect['height'] += loc_iMargin + loc_iToggle;

          // Also adapt the SVG's width and height
          var svg = $(svgDiv).find("svg").first();
          $(svg).attr("width", oRect['width'].toString() + 'px');
          $(svg).attr("height", oRect['height'].toString() + 'px');

          return true;
        } catch (ex) {
          return false;
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
            var rect = $(el).find(".lithium-node").children("rect").first();
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

    // Methods that are exported by [crpstudio.svg] for outside functions
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
        var sHtml = "",   // Html content
            oRect = {},
            i;            // Counter

        try {
          // Validate
          if (svgDiv === undefined ) return false;
          if (errDiv === undefined || errDiv === null) errDiv = svgDiv;
          // Set the local error div
          private_methods.setErrLoc(errDiv);
          private_methods.setSvgRoot(svgDiv);
          private_methods.setNodeTree(oTree);
          // Treat the tree: add parent, level and unique numerical id's
          private_methods.setParentAndId(oTree, null, 0);
          // Other initialisations
          loc_arLeaf = [];
          root = null;
          // Put initial <svg> there
          private_methods.initSvg(svgDiv);
          // Hierarchically build an SVG picture based on [oTree]
          root = private_methods.nodeToSvg(oTree, $(svgDiv).find("svg"));

          // Apply the changes in x,y,w,h to all elements
          private_methods.applyLocations(root, "conn");

          // Calculate a minPoint
          var maxSize = { width: 0, height: 0 };
          // Initialize the maxsizes if root is a lithium-tree
          if ($(root).is(".lithium-tree")) {
            oRect = private_methods.getRect(root);
            maxSize['width'] = oRect['x'] + oRect['width'];
            maxSize['height'] = oRect['y'] + oRect['height'];
          }
          // Walk over all shapes
          $(root).find(".lithium-tree").each(function () {
            if (private_methods.isVisible(this)) {
              var oThisRect = private_methods.getRect(this);
              var iNewWidth = oThisRect['x'] + oThisRect['width'];
              var iNewHeight = oThisRect['y'] + oThisRect['height'];

              // Look for max width / max height
              maxSize['width'] = Math.max(iNewWidth, maxSize['width']);
              maxSize['height'] = Math.max(iNewHeight, maxSize['height']);
            }
          });
          // Adjust the maximum size
          private_methods.setMaxSize(maxSize);

          // Attach an event handler to all the toggles
          $(svgDiv).find(".lithium-toggle rect, line").click(function () { crpstudio.svg.toggle_svg(this); });
          // Attach an event handler to all the NODES
          $(svgDiv).find(".lithium-node").mouseover(function() { crpstudio.svg.node_svg(this, false)});
          $(svgDiv).find(".lithium-node").mouseout(function () { crpstudio.svg.node_stop_svg(this) });
          $(svgDiv).find(".lithium-node").click(function () { crpstudio.svg.node_fix_svg(this) });

          // Return positively
          return true;
        } catch (ex) {
          // Show the error at the indicated place
          $(errDiv).html("treeToSvg error: " + ex.message);
          return null;
        }
      },
      /**
       * toggle
       *    Behaviour when an svg tree is toggled
       * 
       * @param {element} elRect
       * @returns {undefined}
       */
      toggle_svg: function (elRect) {
        var bVisible,   // VIsibility
          sId = "",     // ID as string
          iNodeId=0,    // Node id as integer
          oNode,        // The item from loc_oNode that I am associated with
          elSvg,        // The SVG root of the tree
          elToggle,     // The .lithium-toggle element
          elVbar,       // My own vertical bar
          elTree;       // The tree I am in

        try {
          // Get vertical bar and my tree
          elToggle = $(elRect).parent();                  // This is the "lithium-toggle" <g> element
          elVbar = $(elToggle).children(".lithium-vbar"); // The hidden <g> element under "lithium-toggle"
          elTree = $(elToggle).parent();                  // THis is the parent "lithium-tree" <g> element
          elSvg = $(elRect).closest("svg");               // THis is the root <svg> element of this tree
          // Get my ID
          sId = $(elTree).attr("id");
          iNodeId = parseInt(sId.match(/\d+/g), 10);
          // Get the node with this id
          oNode = private_methods.getNode(loc_oNode, iNodeId);
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
            // Adapt the [expanded] state in the correct oNode
            oNode['expanded'] = true;
          } else {
            // Bar is invisible: show it
            private_methods.classRemove(elVbar, "hidden");
            // Make all children invisible
            $(elTree).find(".lithium-tree").each(function () {
              private_methods.classAdd(this, "hidden");
            });
            // Adapt the [expanded] state in the correct oNode
            oNode['expanded'] = false;
          }
          // Now make sure the whole svg-tree is re-drawn
          crpstudio.svg.treeToSvg($(elSvg).parent(), loc_oNode, loc_errDiv);
        } catch (ex) {
          // Show the error at the indicated place
          $(errDiv).html("toggle_svg error: " + ex.message);
        }
      },

      /**
      * node_svg
      *    Behaviour when there is a mouse-over on one particular node
      * 
      * @param {element} elRect
      * @param {boolean} bGetId
      * @returns {undefined}
      */
      node_svg: function (elRect, bGetId) {
        var iNodeId = 0,  // Node id as integer
            prop,         // Counter
            lHtml = [],   // Where we gather HTML
            oSvg,         // Coordinates of the svg rect element
            elTarget,     // The <div> we want to position
            oNode,        // The item from loc_oNode that I am associated with
            oFeat = {},   // Feature object
            sId = "";     // Identifier of the element that has been hit

        try {
          // Validate: this must be a lithium-node <g> element
          if (!$(elRect).is("g.lithium-node")) {
            return;
          }
          if (loc_bKeep) return;
          // The node must have an identifier
          sId = $(elRect).attr("id");
          iNodeId = parseInt(sId.match(/\d+/g), 10);
          // Are we already there?
          if (iNodeId === loc_iCurrentNode) { return;}
          // Get the node with this id
          oNode = private_methods.getNode(loc_oNode, iNodeId);
          // Get the features in this node
          if (oNode.hasOwnProperty("f")) {
            oFeat = oNode['f'];
            // Convert this into an HTML element
            lHtml.push("<div id='svg-features" + iNodeId.toString() + "' class='svg-features'><table>");
            if (bGetId) {
              lHtml.push("<tr><td class='attrlabel'>id</td><td class='attrvalue'>" + oNode['id'] + "</td></tr>");
              lHtml.push("<tr><td class='attrlabel'>pos</td><td class='attrvalue'>" + oNode['pos'] + "</td></tr>");
            }
            if (Object.keys(oFeat).length === 0) {
              lHtml.push("<tr><td colspan='2'>(this node has no features)</td></tr>");
            } else {
              for (prop in oFeat) {
                if (oFeat.hasOwnProperty(prop)) {
                  lHtml.push("<tr><td class='attrlabel'>" + prop + "</td><td class='attrvalue'>" + oFeat[prop] + "</td></tr>");
                }
              }
            }
            lHtml.push("</table></div>");
            // Add this element at an appropriate place
            $("#sentdetails_feats").html(lHtml.join("\n"));
            elTarget = $("#sentdetails_feats").find(".svg-features").get(0);
            // Get screen coordinates
            oSvg = private_methods.screenCoordsForRect($(elRect).children("rect").first());
            elTarget.style.left = oSvg['x'] + 'px';
            elTarget.style.top = (oSvg['y'] + oSvg['height'] + 10).toString() + 'px';
            $("#sentdetails_feats").removeClass("hidden");
            // Now adjust the position based on the shown div
            oSvg = private_methods.fitFeatureBox(oSvg, elTarget);
            elTarget.style.left = oSvg['x'] + 'px';
            elTarget.style.top = oSvg['y']  + 'px';
          }

        } catch (ex) {
          // Show the error at the indicated place
          $(errDiv).html("node_svg error: " + ex.message);
        }
      },
      node_fix_svg: function (elRect) {
        var elTarget;     // The <div> we want to position

        try {
          if (loc_bKeep) {
            loc_bKeep = false;
            return;
          }
          // Make sure the calculation is done
          crpstudio.svg.node_svg(elRect, true);
          crpstudio.svg.node_stop_svg(elRect);
          // Show the information in the correct place
          elTarget = $("#sentdetails_feats").find(".svg-features").get(0);
          elTarget.style.left =  '10px';
          elTarget.style.top  =  '80px';
          $("#sentdetails_feats").removeClass("hidden");
          loc_bKeep = true;
        } catch (ex) {
          // Show the error at the indicated place
          $(errDiv).html("node_fix_svg error: " + ex.message);
        }
      },
      node_stop_svg: function (elRect) {
        if (!loc_bKeep) {
          $("#sentdetails_feats").addClass("hidden");
          loc_iCurrentNode = -1;
        }
      }


    };
  }($, crpstudio.config));

  return crpstudio;

}(jQuery, window.crpstudio || {}));
