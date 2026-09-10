# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
        #self.nex可以也是ListNode类型

def create_linked_list(arr):
    dummy = ListNode()
    cur = dummy
    for x in arr:
        cur.next = ListNode(x)
        cur = cur.next
    return dummy.next        #True head_node

#解释map是什么意思
# map函数将input().split()返回的字符串列表中的每个元素都转换为整数
l = list(map(int,input().split()))

l1 = create_linked_list(l)
#遍历链表
# d = result
# while d:
#     print(d.val)
#     d = d.next

#反转链表
def reverse_linked_list(cur: ListNode,prev: ListNode) -> ListNode:
    prev = cur.next
    





