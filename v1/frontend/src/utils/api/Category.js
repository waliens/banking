import Model from './Model';

function buildNestedCategoryName(cmap, category) {
  if (category.id_parent) {
    let array = buildNestedCategoryName(cmap, cmap[category.id_parent]);
    array.push(category.name);
    return array;
  } else {
    return new Array(category.name);
  }
}

export default class Category extends Model {
  /** @inheritdoc */
  static get className() {
    return 'category';
  }

  static get collectionName() {
    return 'categories';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.name = null;
    this.id_parent = null;
    this.color = null;
    this.icon = null; 
  }

  static async getCategoryTree() {
    let categories = await Category.fetchAll();
    let map = {};
    let roots = new Array();
    categories.forEach(c => {
      map[c.id] = c;
      map[c.id].children = new Array();
      if (!c.id_parent) {
        roots.push(c.id);
      }
    });
    categories.forEach(c => {
      if (c.id_parent) {
        map[c.id_parent].children.push(c);
      }
    });
    return roots.map(id => map[id]);
  }
 
  /**
   * {
   *  0: [roots...],
   *  1: [children at depth 1...],
   *  2: ...
   * } 
   */
  static async getCategoryTreeByDepth() {
    let tree = await Category.getCategoryTree();
    let map = {};
    let byDepth = {};
    let collectDepths = (nodes, currDepth) => {
      if (!byDepth[currDepth]) {
        byDepth[currDepth] = new Array();
      }
      byDepth[currDepth] = [...byDepth[currDepth], ...nodes];
      nodes.forEach(c => {
        map[c.id] = c;
        if (c.id_parent) {
          c.nestedName = [map[c.id_parent].nestedName, c.name].join(" > ")
        } else {
          c.nestedName = c.name;
        }
      });
      nodes.forEach(c => {
        collectDepths(c.children, currDepth+1);
      });
    };
    collectDepths(tree.filter(c => !c.id_parent), 0);
    return byDepth; 
  }

  /**
   * Example: {
   *   id1: {
   *     id: id1,
   *     name: name1,
   *     children: [{id: ...}]
   *   },
   *   id2: {
   *     id: id2,
   *     name: name2,
   *     children: [{id: ...}]
   *   },
   *   [...]
   * }
   */
  static async getFlattenedCategoryTree() {
    let categories = await Category.fetchAll();
    let leaves = new Set(categories.map(c => c.id));
    let map = {};
    categories.forEach(c => {
      map[c.id] = c;
      if (c.id_parent) {
        leaves.delete(c.id_parent);
      }
    });
    let flattened = {};
    leaves.forEach(cid => {
      let current = map[cid];
      let parent = map[current.id_parent];
      // if a leave with no parent 
      if (!parent) {
        current.children = new Array();
        current.nestedName = current.name;
        flattened[current.id] = current;
        return;
      }
      if (!flattened[parent.id]) {
        flattened[parent.id] = parent;
        parent.children = new Array();
        parent.nestedName = buildNestedCategoryName(map, parent).join(" > ");
      }
      parent.children.push(map[cid]);
    });
    return Object.values(flattened);
  }

  static getStringBreadcrumbs(tree=[]) {
    if (!tree || tree.length == 0) {
      return [];
    }
    return Category.getStringBreadcrumbsRecursive(tree);
  }

  static getStringBreadcrumbsRecursive(nodes) {
    if (nodes.length == 0) {
      return [];
    }
    let currentBreadcrumbs = [];
    for (let nodeIdx in nodes) {
      let node = nodes[nodeIdx];
      let childrenBreadcrumbs = Category.getStringBreadcrumbsRecursive(node.children);

      for (let childBrcmbIdx in childrenBreadcrumbs) {
        let childBrcmb = childrenBreadcrumbs[childBrcmbIdx];
        childBrcmb.breadcrumb = [node.name, childBrcmb.breadcrumb].join(" > ")
        currentBreadcrumbs.push(childBrcmb);
      }
      currentBreadcrumbs.push({id: node.id, breadcrumb: node.name })
    }
    return currentBreadcrumbs;
  }
}