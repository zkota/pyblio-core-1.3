<?xml version="1.0" encoding="utf-8"?><!-- -*- nxml -*- -->

<pyblio-schema id="org.pybliographer/wok/0.1">
 <name>Data from Web of Knowledge</name>

 <attribute id="ut" type="id">
  <name>ISI unique identifier</name>
 </attribute>

 <attribute id="doi" type="id">
  <name>DOI</name>
 </attribute>

 <attribute id="author" type="person">
   <name>Authors</name>
 </attribute>

 <attribute id="ref" type="id">
   <name>References</name>
 </attribute>

 <attribute id="abstract" type="text">
   <name>Abstract</name>
 </attribute>

 <attribute id="keyword" type="text">
   <name>Keywords</name>
 </attribute>

 <attribute id="keyword-plus" type="text">
   <name>ISI-Generated Keywords</name>
 </attribute>

 <attribute id="doctype" type="txo" group="doctype">
   <name>Document type</name>
 </attribute>

 <attribute id="source" type="text">
   <name>Source Title</name>
   <qualifiers>
     <attribute id="abbrev" type="text">
       <name>Abbreviated name</name>
     </attribute>
     <attribute id="series" type="text">
       <name>Series</name>
     </attribute>
     <attribute id="pages" type="text">
       <name>Pages</name>
     </attribute>
     <attribute id="volume" type="text">
       <name>Volume</name>
     </attribute>
     <attribute id="number" type="text">
       <name>Number</name>
     </attribute>
     <attribute id="year" type="text">
       <name>Year</name>
     </attribute>
     <attribute id="issn" type="id">
       <name>ISSN</name>
     </attribute>
   </qualifiers>
 </attribute>

 <attribute id="title" type="text">
   <name>Title</name>
 </attribute>

 <attribute id="article_no" type="text">
   <name>Article #</name>
 </attribute>
 
<!--
2	Abstract of Published Item
A	Art Exhibit Review
@	Article
7	Bibliography
I	Biographical-Item
B	Book Review
K	Chronology
C	Correction
C	Correction, Addition
Z	Dance Performance Review
0	Database Review
D	Discussion
E	Editorial Material
X	Excerpt
O	Fiction, Creative Prose
F	Film Review
8	Hardware Review
I	Item About an Individual
L	Letter
M,MC	Meeting Abstract
J	Music Performance Review
S	Music Score
G	Music Score Review
5	News Item
N	Note
Y	Poetry
H	Record Review
6	Reprint
R	Review
Q	Script
9	Software Review
V	TV Review, Radio Review
V	TV Review, Radio Review, Video
T	Theater Review
-->

 <txo-group id="doctype">
   <txo-item id="1">
     <name lang="C">2</name>
     <name>Abstract of Published Item</name>
   </txo-item>
   <txo-item id="2">
     <name lang="C">A</name>
     <name>Art Exhibit Review</name>
   </txo-item>
   <txo-item id="3">
     <name lang="C">@</name>
     <name>Article</name>
   </txo-item>
   <txo-item id="4">
     <name lang="C">7</name>
     <name>Bibliography</name>
   </txo-item>
   <txo-item id="5">
     <name lang="C">I</name>
     <name>Biographical Item</name>
   </txo-item>
   <txo-item id="6">
     <name lang="C">B</name>
     <name>Book review</name>
   </txo-item>
   <txo-item id="7">
     <name lang="C">K</name>
     <name>Chronology</name>
   </txo-item>
   <txo-item id="8">
     <name lang="C">C</name>
     <name>Correction</name>
   </txo-item>
   <txo-item id="9">
     <name lang="C">Z</name>
     <name>Dance Performance Review</name>
   </txo-item>
   <txo-item id="10">
     <name lang="C">0</name>
     <name>Database Review</name>
   </txo-item>
   <txo-item id="11">
     <name lang="C">D</name>
     <name>Discussion</name>
   </txo-item>
   <txo-item id="12">
     <name lang="C">E</name>
     <name>Editorial Material</name>
   </txo-item>
   <txo-item id="13">
     <name lang="C">X</name>
     <name>Excerpt</name>
   </txo-item>
   <txo-item id="14">
     <name lang="C">O</name>
     <name>Fiction, Creative Prose</name>
   </txo-item>
   <txo-item id="15">
     <name lang="C">F</name>
     <name>Film Review</name>
   </txo-item>
   <txo-item id="16">
     <name lang="C">8</name>
     <name>Hardware Review</name>
   </txo-item>
   <txo-item id="17">
     <name lang="C">L</name>
     <name>Letter</name>
   </txo-item>
   <txo-item id="18">
     <name lang="C">M</name>
     <name>Meeting Abstract</name>
   </txo-item>
   <txo-item id="19">
     <name lang="C">J</name>
     <name>Music Performance Review</name>
   </txo-item>
   <txo-item id="20">
     <name lang="C">S</name>
     <name>Music Score</name>
   </txo-item>
   <txo-item id="21">
     <name lang="C">G</name>
     <name>Music Score Review</name>
   </txo-item>
   <txo-item id="22">
     <name lang="C">5</name>
     <name>News item</name>
   </txo-item>
   <txo-item id="23">
     <name lang="C">N</name>
     <name>Note</name>
   </txo-item>
   <txo-item id="24">
     <name lang="C">Y</name>
     <name>Poetry</name>
   </txo-item>
   <txo-item id="25">
     <name lang="C">H</name>
     <name>Record Review</name>
   </txo-item>
   <txo-item id="26">
     <name lang="C">6</name>
     <name>Reprint</name>
   </txo-item>
   <txo-item id="27">
     <name lang="C">R</name>
     <name>Review</name>
   </txo-item>
   <txo-item id="28">
     <name lang="C">Q</name>
     <name>Script</name>
   </txo-item>
   <txo-item id="29">
     <name lang="C">9</name>
     <name>Software Review</name>
   </txo-item>
   <txo-item id="30">
     <name lang="C">V</name>
     <name>TV Review, Radio Review</name>
   </txo-item>
   <txo-item id="31">
     <name lang="C">T</name>
     <name>Theater Review</name>
   </txo-item>
 </txo-group>
</pyblio-schema>
