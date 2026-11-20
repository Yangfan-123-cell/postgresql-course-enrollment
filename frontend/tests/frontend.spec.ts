import { test, expect, type Page } from "@playwright/test";
async function login(page: Page, account = "S0001") {
  await page.goto("/login");
  await page.getByLabel("账号", { exact: true }).fill(account);
  await page.getByLabel("密码", { exact: true }).fill("Passw0rd!");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page).toHaveURL(account === "admin" ? /\/admin$/ : /\/hall$/);
}
test("学生登录、201 选课、202 候补、课表、退课与放弃候补", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "登录选课系统" })).toBeVisible();
  await page.screenshot({ path: "test-results/login-desktop.png", fullPage: true });
  await login(page);
  await expect(page.locator(".course-card")).toHaveCount(9);
  await page
    .locator(".course-card")
    .filter({ hasText: "高级数据库系统" })
    .getByRole("button", { name: "选择课程", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("已选中");
  await page
    .locator(".course-card")
    .filter({ hasText: "机器学习" })
    .getByRole("button", { name: "加入候补", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("当前第 4 位");
  await page.screenshot({
    path: "test-results/hall-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "每周课表", exact: true }).click();
  await expect(page.locator(".timetable-course")).toContainText(
    "高级数据库系统",
  );
  await page.screenshot({
    path: "test-results/timetable-desktop.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "我的课程", exact: true }).click();
  await page.getByRole("button", { name: "退课", exact: true }).click();
  await page.getByRole("button", { name: "确认退课" }).click();
  await expect(page.getByRole("status")).toContainText("退课成功");
  await expect(page.locator("tbody tr")).toHaveCount(0);
  await page.getByRole("link", { name: "候补队列", exact: true }).click();
  await expect(page.locator(".queue-position strong")).toHaveText("4");
  await page.getByRole("button", { name: "放弃候补", exact: true }).click();
  await page.getByRole("button", { name: "确认放弃" }).click();
  await expect(page.getByRole("status")).toContainText("已退出候补");
  await expect(page.locator(".course-card")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("选课单规划、列表视图、学业概览与通知中心", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page);
  await page.getByRole("button", { name: "通知公告" }).click();
  await expect(page.locator(".notice-dropdown")).toBeVisible();
  await page.keyboard.press("Escape");

  // 收藏两门课进选课单，再切换列表视图检查
  await page
    .locator(".course-card")
    .filter({ hasText: "高级数据库系统" })
    .getByRole("button", { name: "加入选课单" })
    .click();
  await page
    .locator(".course-card")
    .filter({ hasText: "分布式系统" })
    .getByRole("button", { name: "加入选课单" })
    .click();

  await page.getByRole("button", { name: "列表", exact: true }).click();
  await expect(page.locator(".list-table tbody tr")).toHaveCount(9);
  await page.getByRole("button", { name: "卡片", exact: true }).click();

  await page.getByRole("link", { name: /选课单/ }).first().click();
  await expect(page).toHaveURL(/\/cart$/);
  await expect(page.locator(".cart-card")).toHaveCount(2);
  await page.screenshot({ path: "test-results/cart-desktop.png", fullPage: true });

  await page.getByRole("button", { name: /一键提交/ }).click();
  await expect(page.getByRole("status")).toContainText("2 门选课成功");

  await page.getByRole("link", { name: "学业概览", exact: true }).click();
  await expect(page.locator(".ring-label strong")).toHaveText("7");
  await page.screenshot({ path: "test-results/overview-desktop.png", fullPage: true });
  expect(errors).toEqual([]);
});

test("搜索、分页、无结果、移动端和登录恢复", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "下一页" }).click();
  await expect(page.locator(".course-card")).toHaveCount(3);
  await page.getByLabel("搜索课程", { exact: true }).fill("不存在的课程");
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await expect(
    page.getByText("暂无匹配课程，试试调整搜索条件。"),
  ).toBeVisible();
  await page.getByLabel("搜索课程", { exact: true }).fill("数据库");
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await expect(page.locator(".course-card")).toHaveCount(1);
  await page.reload();
  await expect(page.getByRole("heading", { name: "选课大厅" })).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".course-card").first()).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({ path: "test-results/hall-mobile.png" });
});
test("401 错误与角色路由限制", async ({ page }) => {
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("账号", { exact: true }).fill("S0001");
  await page.getByLabel("密码", { exact: true }).fill("wrong");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("账号或密码错误");
  await page.getByLabel("密码", { exact: true }).fill("Passw0rd!");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page).toHaveURL(/\/hall$/);
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/hall$/);
  await page.evaluate(() =>
    sessionStorage.setItem("course-enrollment-token", "expired"),
  );
  await page.getByRole("link", { name: "我的课程", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
});
test("满员拒绝候补、重复选课及冲突错误的详情展示", async ({ page }) => {
  await login(page);
  await page.goto("/sections/2");
  await page.getByLabel("满员时同意加入候补").uncheck();
  await page.getByRole("button", { name: "提交选课" }).click();
  await expect(page.getByRole("alert")).toContainText("已满");
  await page.goto("/sections/1");
  await page.getByRole("button", { name: "提交选课" }).click();
  await expect(page.getByRole("status")).toContainText("选课成功");
  await page.getByRole("button", { name: "提交选课" }).click();
  await expect(page.getByRole("alert")).toContainText("已选");
  // 使用页面内导航，避免整页重载重置内存演示数据。
  await page.getByRole("link", { name: "返回选课大厅" }).click();
  await page.getByRole("button", { name: "下一页" }).click();
  await page.locator(".course-card").filter({ hasText: "并发编程" }).getByRole("link", { name: "查看详情" }).click();
  await page.getByRole("button", { name: "提交选课" }).click();
  await expect(page.getByRole("alert")).toContainText("时间冲突");
  await expect(page.getByRole("alert")).toContainText("高级数据库系统");
});
test("管理员创建编辑课程、教学班校验、名单导出与选课开关", async ({ page }) => {
  await login(page, "admin");
  await page.getByRole("button", { name: "新建课程", exact: true }).click();
  const form = page.getByRole("dialog");
  await form.getByLabel("课程号", { exact: true }).fill("TEST101");
  await form.getByLabel("课程名", { exact: true }).fill("Agent Memory");
  await form.getByRole("button", { name: "保存", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("保存成功");
  const course = page.locator("tbody tr").filter({ hasText: "TEST101" });
  await course.getByRole("button", { name: "编辑" }).click();
  await form.getByLabel("课程名", { exact: true }).fill("Agent Memory 实验");
  await form.getByRole("button", { name: "保存", exact: true }).click();
  await expect(course).toContainText("Agent Memory 实验");
  const id = Number(
    (await course.locator("small").textContent())!.replace("ID ", ""),
  );
  await page.getByRole("button", { name: "教学班管理", exact: true }).click();
  await expect(page.locator("tbody tr")).toHaveCount(12);
  await page.getByRole("button", { name: "新建教学班", exact: true }).click();
  await form.getByLabel("课程 ID", { exact: true }).fill(String(id));
  await form.getByLabel("授课教师", { exact: true }).fill("测试教师");
  await form.getByRole("button", { name: "添加时间段" }).click();
  await form.getByRole("button", { name: "保存", exact: true }).click();
  await expect(form.getByRole("alert")).toContainText("不能重叠");
  await form.getByLabel("周几", { exact: true }).nth(1).fill("3");
  await form.getByRole("button", { name: "保存", exact: true }).click();
  await expect(page.locator("tbody tr")).toHaveCount(13);
  await page
    .locator("tbody tr")
    .first()
    .getByRole("button", { name: "编辑", exact: true })
    .click();
  await form.getByLabel("容量", { exact: true }).fill("1");
  await form.getByRole("button", { name: "保存", exact: true }).click();
  await expect(form.getByRole("alert")).toContainText("容量不能小于");
  await form.getByLabel("容量", { exact: true }).fill("80");
  await form.getByRole("button", { name: "保存", exact: true }).click();
  await expect(page.locator("tbody tr").first()).toContainText("25 / 80");
  await page
    .locator("tbody tr")
    .first()
    .getByRole("button", { name: "名单", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("杨帆");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "导出 CSV" }).click();
  expect((await download).suggestedFilename()).toBe("section_1_roster.csv");
  await page.getByRole("button", { name: "关闭", exact: true }).click();
  await page.getByRole("button", { name: "关闭选课", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("已关闭");
  await page.getByRole("button", { name: "开放选课", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("已开放");
  await page.screenshot({
    path: "test-results/admin-desktop.png",
    fullPage: true,
  });
});
