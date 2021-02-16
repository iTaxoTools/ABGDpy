params = {
  "general": {
    "label": "General",
    "fields": {
      "mega": {
        "label":    "MEGA CVS",
        "doc":      "If True, the distance Matrix is supposed to be MEGA CVS\n(other formats are guessed).",
        "type":     "bool",
        "default":  False
      },
      "spart": {
        "label":    "Generate Spart",
        "doc":      "Generate Spart files.",
        "type":     "bool",
        "default":  True
      },
      "simple": {
        "label":    "Generate Partitions",
        "doc":      "Generate partition files.",
        "type":     "bool",
        "default":  True
      },
      "all": {
        "label":    "Generate Trees",
        "doc":      "Generate all partitions and tree files.",
        "type":     "bool",
        "default":  False
      }
    }
  },
  "prior": {
    "label": "Divergence",
    "doc": "Prior Intraspecific Divergence",
    "fields": {
      "min": {
        "label":    "Pmin",
        "doc":      "Minimal a priori value.",
        "type":     "float",
        "default":  0.001
      },
      "max": {
        "label":    "Pmax",
        "doc":      "Maximal a priori value.",
        "type":     "float",
        "default":  0.1
      },
      "steps": {
        "label":    "Steps",
        "doc":      "Number of examined steps in the range of [Pmin, Pmax].",
        "type":     "int",
        "default":  10
      },
      "slope": {
        "label":    "X",
        "doc":      "Proxy for the minimum relative gap width; the minimum slope increase.",
        "type":     "float",
        "default":  1.5
      }
    }
  },
  "distance": {
    "label": "Distance",
    "fields": {
      "method": {
        "label":    "Method",
        "doc":      "If you enter a fasta file you can select your distance.",
        "type":     "list",
        "default":  1,
        "data": {
          "items":  [0,1,3],
          "labels": ["Jukes-Cantor (JC69)","Kimura (K80)","Simple Distance"]
          }
      },
      "rate": {
        "label":    "Kimura TS/TV",
        "doc":      "Transition/transversion for Kimura 3-P distance.",
        "type":     "float",
        "default":  2.0
      }
    }
  }
}
