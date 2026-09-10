class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        l = len(nums)
        for i in range(l):
            if ((target - nums[i]) in nums )and (i != nums.index(target - nums[i])):
                return [i,nums.index(target - nums[i])]