"""
Based on the Jos Stam paper https://www.researchgate.net/publication/2560062_Real-Time_Fluid_Dynamics_for_Games
and the mike ash vulgarization https://mikeash.com/pyblog/fluid-simulation-for-dummies.html
"""
import numpy as np
import math
import imageio


class Fluid:

    def __init__(self):
        self.size = 40  # map size
        self.dt = 0.2  # time interval
        self.iter = 2  # linear equation solving iteration number

        self.diff = 0.0000
        self.visc = 0.0000  # viscosity

        self.s = np.full((self.size, self.size), 0, dtype=float)
        self.density = np.full((self.size, self.size), 0, dtype=float)

        # array of 2d vectors, [x, y]
        self.velo = np.full((self.size, self.size, 2), 0, dtype=float)
        self.velo0 = np.full((self.size, self.size, 2), 0, dtype=float)

    def step(self):
        self.diffuse(self.velo0, self.velo, self.visc)  # x axis

        # x0, y0, x, y
        self.project(self.velo0[:, :, 0], self.velo0[:, :, 1], self.velo[:, :, 0], self.velo[:, :, 1])

        self.advect(self.velo[:, :, 0], self.velo0[:, :, 0], self.velo0[:, :, 0], self.velo0[:, :, 1])
        self.advect(self.velo[:, :, 1], self.velo0[:, :, 1], self.velo0[:, :, 0], self.velo0[:, :, 1])

        self.project(self.velo[:, :, 0], self.velo[:, :, 1], self.velo0[:, :, 0], self.velo0[:, :, 1])

        self.diffuse(self.s, self.density, self.diff)
        self.advect(self.density, self.s, self.velo[:, :, 0], self.velo[:, :, 1])

    def lin_solve(self, x, x0, a, c):
        c_recip = 1 / c

        for iteration in range(0, self.iter):
            for j in range(1, self.size - 1):
                for i in range(1, self.size - 1):
                    x[i, j] = (x0[i, j] + a * (x[i + 1, j] + x[i - 1, j] + x[i, j + 1] + x[i, j - 1])) * c_recip

            self.set_boundaries(x)

    def set_boundaries(self, table):
        """
        Boundaries handling
        :return:
        """

        if len(table.shape) > 2:  # 3d velocity vector array
            # vertical, invert if y vector
            table[:, 0, 1] = - table[:, 0, 1]
            table[:, self.size - 1, 1] = - table[:, self.size - 1, 1]

            # horizontal, invert if x vector
            table[0, :, 0] = - table[0, :, 0]
            table[self.size - 1, :, 0] = - table[self.size - 1, :, 0]

        table[0, 0] = 0.5 * (table[1, 0] + table[0, 1])
        table[0, self.size - 1] = 0.5 * (table[1, self.size - 1] + table[0, self.size - 2])
        table[self.size - 1, 0] = 0.5 * (table[self.size - 2, 0] + table[self.size - 1, 1])
        table[self.size - 1, self.size - 1] = 0.5 * table[self.size - 2, self.size - 1]\
                                              + table[self.size - 1, self.size - 2]

    def diffuse(self, x, x0, diff):
        a = self.dt * diff * (self.size - 2) * (self.size - 2)
        self.lin_solve(x, x0, a, 1 + 6 * a)

    def project(self, velo_x, velo_y, p, div):
        for j in range(1, self.size - 1):
            for i in range(1, self.size - 1):
                div[i, j] = -0.5 * (
                        velo_x[i + 1, j] -
                        velo_x[i - 1, j] +
                        velo_y[i, j + 1] -
                        velo_y[i, j - 1]) / self.size

                p[i, j] = 0

        self.set_boundaries(div)
        self.set_boundaries(p)
        self.lin_solve(p, div, 1, 6)

        for j in range(1, self.size - 1):
            for i in range(1, self.size - 1):
                velo_x[i, j] -= 0.5 * (p[i + 1, j] - p[i - 1, j]) * self.size
                velo_y[i, j] -= 0.5 * (p[i, j + 1] - p[i, j - 1]) * self.size

        self.set_boundaries(self.velo)

    def advect(self, d, d0, velo_x, velo_y):
        dtx = self.dt * (self.size - 2)
        dty = self.dt * (self.size - 2)

        for j in range(1, self.size - 1):
            for i in range(1, self.size - 1):

                tmp1 = dtx * velo_x[i, j]
                tmp2 = dty * velo_y[i, j]
                x = i - tmp1
                y = j - tmp2

                if x < 0.5: x = 0.5
                if x > self.size + 0.5: x = self.size + 0.5
                i0 = math.floor(x)
                i1 = i0 + 1.0

                if y < 0.5: y = 0.5
                if y > self.size + 0.5: y = self.size + 0.5
                j0 = math.floor(y)
                j1 = j0 + 1.0

                s1 = x - i0
                s0 = 1.0 - s1
                t1 = y - j0
                t0 = 1.0 - t1

                i0i = int(i0)
                i1i = int(i1)
                j0i = int(j0)
                j1i = int(j1)

                d[i, j] = s0 * (t0 * d0[i0i, j0i] + t1 * d0[i0i, j1i]) + \
                          s1 * (t0 * d0[i1i, j0i] + t1 * d0[i1i, j1i])

        self.set_boundaries(d)


if __name__ == "__main__":

    frames = 30

    flu = Fluid()

    video = np.full((frames, flu.size, flu.size), 0, dtype=float)

    for step in range(0, frames):
        flu.density[4:7, 4:7] += 100  # add density into a 3*3 square
        flu.velo[5, 5] += [1, 2]

        flu.step()
        video[step] = flu.density

    imageio.mimsave('./video.gif', video.astype('uint8'))
