#! /bin/bash

{
  ovs-vsctl show
} | awk '
{
  gsub("\"","",$2)
  if ($1 == "Bridge") {
    BR=$2
    BRIDGES[BR]++	
  } else if ($1 == "Port") {
    PT=$2
    if (PT ~ /br/) {
      PORTS[BR,PT]++ 
    } else if (PT ~ /vnet/) {
      VNET[BR,PT]++
    } else {
      NIC[BR,PT]++
    }
  } else if ($1 == "tag:") {
    TAG[BR,PT]=$2
  }
}

END {
    printf "BR----SubBR-----TAG---VNET(s)/NIC(s)---------------------\n"
    for (c in BRIDGES) {
      #BRIDGE
      printf "%-6s", c 
      printf "%-10s", " "
      printf "%-6s", " "
      for (n in NIC) {
        split(n, sepn, "\034")
        if (sepn[1]==c) {
          #NIC
          #printf "\t\t\t%s",sepn[2]
          printf "%s",sepn[2]
        }
      }
      printf "\n"
      for (p in PORTS) {
        split(p, sepp, "\034")
        if (sepp[1]==c) {
          if (sepp[2]==c) {
            #SUBBRIDGE with BRIDGE name
            #printf "\t%s\t\t", sepp[2] 
            printf "%-6s", " "
            printf "%-10s", sepp[2]
            printf "%-6s", " "
            for (v in VNET) {
              split(v, sepv, "\034")
              if (sepv[1]==c && TAG[v]=="") {
                printf "%s ", sepv[2]
              }
            }
            printf "\n"
          } else {
            #printf "\t%s\t%s\t", sepp[2], TAG[c,sepp[2]] 
            printf "%-6s", " "
            printf "%-10s", sepp[2]
            printf "%-6s", TAG[c,sepp[2]]
            for (v in VNET) {
              split(v, sepv, "\034")
              if (TAG[c,sepp[2]] == TAG[c,sepv[2]]) {
                printf "%s ", sepv[2]
              }
            }
            printf "\n"
          }
        }
      }
      printf "---------------------------------------------------------\n"
    }
    print
}
'
